"""
Speechmatics real-time transcription service.
Handles audio streaming and transcription using Speechmatics WebSocket API.
"""

import asyncio
import logging
from typing import Callable, Optional
import speechmatics
from speechmatics.models import (
    ConnectionSettings,
    AudioSettings,
    TranscriptionConfig,
    ServerMessageType
)
from httpx import HTTPStatusError
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class SpeechmaticsService:
    """
    Service for real-time audio transcription using Speechmatics.
    Manages WebSocket connections and handles transcription events.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        connection_url: Optional[str] = None,
        language: str = "en"
    ):
        """
        Initialize the Speechmatics transcription service.

        Args:
            api_key: Speechmatics API key (defaults to env var)
            connection_url: WebSocket connection URL (defaults to env var)
            language: Language code for transcription (default: "en")
        """
        self.api_key = api_key or settings.SPEECHMATICS_API_KEY
        self.connection_url = connection_url or settings.CONNECTION_URL
        self.language = language or settings.SPEECHMATICS_LANGUAGE

        if not self.api_key:
            raise ValueError("Speechmatics API key is required")

        self.ws_client: Optional[speechmatics.client.WebsocketClient] = None
        self.is_running = False

        # Event handlers
        self.on_partial_transcript: Optional[Callable] = None
        self.on_final_transcript: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

    def _create_client(self) -> speechmatics.client.WebsocketClient:
        """
        Create a new Speechmatics WebSocket client.

        Returns:
            Configured WebSocket client
        """
        connection_settings = ConnectionSettings(
            url=self.connection_url,
            auth_token=self.api_key,
        )

        return speechmatics.client.WebsocketClient(connection_settings)

    def _setup_event_handlers(self, ws_client: speechmatics.client.WebsocketClient):
        """
        Set up event handlers for the WebSocket client.

        Args:
            ws_client: The WebSocket client to configure
        """
        # Partial transcript handler
        def handle_partial_transcript(msg):
            if self.on_partial_transcript:
                transcript = msg.get('metadata', {}).get('transcript', '')
                logger.debug(f"[Partial] {transcript}")
                asyncio.create_task(self.on_partial_transcript(transcript, is_final=False))

        # Final transcript handler
        def handle_final_transcript(msg):
            if self.on_final_transcript:
                transcript = msg.get('metadata', {}).get('transcript', '')
                logger.info(f"[Final] {transcript}")
                asyncio.create_task(self.on_final_transcript(transcript, is_final=True))

        # Register handlers
        ws_client.add_event_handler(
            event_name=ServerMessageType.AddPartialTranscript,
            event_handler=handle_partial_transcript
        )

        ws_client.add_event_handler(
            event_name=ServerMessageType.AddTranscript,
            event_handler=handle_final_transcript
        )

    async def start_transcription(
        self,
        audio_stream,
        on_partial: Optional[Callable] = None,
        on_final: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        enable_partials: bool = True,
        max_delay: float = 1.0,
        operating_point: str = "enhanced"
    ):
        """
        Start real-time transcription from an audio stream.

        Args:
            audio_stream: Async generator or iterable yielding audio chunks
            on_partial: Callback for partial transcripts (async function)
            on_final: Callback for final transcripts (async function)
            on_error: Callback for errors (async function)
            enable_partials: Whether to enable partial transcripts
            max_delay: Maximum delay for transcription (seconds)
            operating_point: Speechmatics operating point ("enhanced" or "standard")
        """
        try:
            # Set callbacks
            self.on_partial_transcript = on_partial
            self.on_final_transcript = on_final
            self.on_error = on_error

            # Create WebSocket client
            self.ws_client = self._create_client()
            self._setup_event_handlers(self.ws_client)

            # Configure audio settings
            audio_settings = AudioSettings()

            # Configure transcription settings
            transcription_config = TranscriptionConfig(
                operating_point=operating_point,
                language=self.language,
                enable_partials=enable_partials,
                max_delay=max_delay,
            )

            logger.info("Starting Speechmatics transcription...")
            self.is_running = True

            # Run transcription synchronously (Speechmatics SDK requirement)
            # This is a blocking call, so it should run in an executor or separate thread
            await asyncio.to_thread(
                self.ws_client.run_synchronously,
                audio_stream,
                transcription_config,
                audio_settings
            )

        except HTTPStatusError as e:
            error_msg = f"HTTP error during transcription: {e}"
            logger.error(error_msg)
            if e.response.status_code == 401:
                error_msg = "Invalid Speechmatics API key"
            if self.on_error:
                await self.on_error(error_msg)
            raise

        except Exception as e:
            error_msg = f"Error during transcription: {str(e)}"
            logger.error(error_msg)
            if self.on_error:
                await self.on_error(error_msg)
            raise

        finally:
            self.is_running = False
            logger.info("Transcription stopped")

    def stop_transcription(self):
        """
        Stop the ongoing transcription.
        """
        self.is_running = False
        logger.info("Stopping transcription...")
        # Note: Speechmatics SDK doesn't have explicit stop method
        # Connection will be closed when audio stream ends


class AudioStreamAdapter:
    """
    Adapter to convert WebSocket audio chunks into a stream compatible with Speechmatics.
    """

    def __init__(self):
        self.queue = asyncio.Queue()
        self.is_active = True

    async def add_chunk(self, chunk: bytes):
        """Add an audio chunk to the stream."""
        if self.is_active:
            await self.queue.put(chunk)

    async def close(self):
        """Close the stream."""
        self.is_active = False
        await self.queue.put(None)  # Sentinel value

    def __iter__(self):
        """Make the adapter iterable for Speechmatics SDK."""
        return self

    def __next__(self):
        """
        Get the next chunk synchronously.
        This is required by Speechmatics SDK which expects a synchronous iterator.
        """
        try:
            # Use asyncio.run_coroutine_threadsafe or similar for thread-safe access
            # For now, we'll use get_nowait and handle empty queue
            chunk = self.queue.get_nowait()
            if chunk is None:
                raise StopIteration
            return chunk
        except asyncio.QueueEmpty:
            # Return empty bytes to keep the stream alive
            return b''