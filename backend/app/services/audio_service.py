"""
Audio service module for Speech-to-Text (STT) integration.
Handles audio transcription using OpenAI Whisper API.
"""

import io
import asyncio
from typing import Optional, AsyncIterator
from openai import AsyncOpenAI
from app.config import settings


class AudioService:
    """
    Service for handling audio transcription via OpenAI Whisper API.

    Features:
    - Real-time audio buffering
    - Automatic format conversion
    - Streaming transcription support
    """

    def __init__(self):
        """Initialize the AudioService with OpenAI client."""
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for audio transcription")

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value()
        )

        # Audio buffer configuration
        self.buffer_duration_ms = 2000  # Buffer 2 seconds before transcribing
        self.sample_rate = 16000  # 16kHz for optimal Whisper performance
        self.channels = 1  # Mono audio

    async def transcribe_audio(
        self,
        audio_data: bytes,
        format: str = "webm",
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio data using OpenAI Whisper API.

        Args:
            audio_data: Raw audio bytes
            format: Audio format (webm, wav, mp3, etc.)
            language: Optional language code (e.g., 'en', 'es')

        Returns:
            str: Transcribed text

        Raises:
            Exception: If transcription fails
        """
        try:
            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{format}"

            # Call Whisper API
            print(f"🎤 Transcribing {len(audio_data)} bytes of audio ({format} format)...")

            transcription = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="text"
            )

            print(f"✅ Transcription complete: {transcription[:100]}...")
            return transcription

        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")

    async def transcribe_streaming(
        self,
        audio_chunks: AsyncIterator[bytes],
        chunk_duration_ms: int = 2000
    ) -> AsyncIterator[str]:
        """
        Transcribe streaming audio in chunks.

        This method buffers incoming audio chunks and transcribes them
        in batches to balance latency vs. accuracy.

        Args:
            audio_chunks: Async iterator of audio byte chunks
            chunk_duration_ms: Duration to buffer before transcription

        Yields:
            str: Transcribed text segments
        """
        buffer = bytearray()

        async for chunk in audio_chunks:
            buffer.extend(chunk)

            # Check if buffer has enough data (simple byte count heuristic)
            # More sophisticated: calculate based on sample rate + duration
            if len(buffer) >= 32000:  # ~2 seconds at 16kHz mono 16-bit
                try:
                    # Transcribe the buffered audio
                    text = await self.transcribe_audio(bytes(buffer), format="webm")

                    if text.strip():  # Only yield non-empty transcriptions
                        yield text

                    # Clear buffer after successful transcription
                    buffer.clear()

                except Exception as e:
                    print(f"⚠️ Streaming transcription error: {e}")
                    # Continue streaming even if one chunk fails
                    buffer.clear()

        # Process any remaining audio in buffer
        if len(buffer) > 0:
            try:
                text = await self.transcribe_audio(bytes(buffer), format="webm")
                if text.strip():
                    yield text
            except Exception as e:
                print(f"⚠️ Final chunk transcription error: {e}")


class AudioBuffer:
    """
    Thread-safe audio buffer for accumulating audio chunks.
    """

    def __init__(self, max_size_bytes: int = 10_000_000):  # 10MB max
        """
        Initialize audio buffer.

        Args:
            max_size_bytes: Maximum buffer size before overflow error
        """
        self.buffer = bytearray()
        self.max_size = max_size_bytes
        self.lock = asyncio.Lock()

    async def append(self, data: bytes):
        """
        Append audio data to buffer.

        Args:
            data: Audio bytes to append

        Raises:
            BufferError: If buffer exceeds max size
        """
        async with self.lock:
            if len(self.buffer) + len(data) > self.max_size:
                raise BufferError(f"Audio buffer overflow (max: {self.max_size} bytes)")
            self.buffer.extend(data)

    async def get_and_clear(self) -> bytes:
        """
        Get all buffered data and clear the buffer.

        Returns:
            bytes: All accumulated audio data
        """
        async with self.lock:
            data = bytes(self.buffer)
            self.buffer.clear()
            return data

    async def size(self) -> int:
        """Get current buffer size in bytes."""
        async with self.lock:
            return len(self.buffer)

    async def clear(self):
        """Clear the buffer."""
        async with self.lock:
            self.buffer.clear()