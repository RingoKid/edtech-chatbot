"""
WebSocket endpoint for real-time audio transcription using Speechmatics.
Frontend sends audio chunks, backend transcribes and sends back text.
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.speechmatics_service import SpeechmaticsService
import json
import io

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


class AudioStreamBuffer:
    """
    Buffer for collecting audio chunks from WebSocket and providing them
    to the Speechmatics service as a synchronous iterator.
    """

    def __init__(self):
        self.chunks = []
        self.is_active = True
        self.lock = asyncio.Lock()

    async def add_chunk(self, chunk: bytes):
        """Add an audio chunk to the buffer."""
        async with self.lock:
            if self.is_active:
                self.chunks.append(chunk)

    async def close(self):
        """Close the stream."""
        async with self.lock:
            self.is_active = False

    def __iter__(self):
        """Make the buffer iterable for Speechmatics SDK."""
        return self

    def __next__(self):
        """
        Get the next chunk synchronously.
        This is required by Speechmatics SDK which expects a synchronous iterator.
        """
        # Wait for chunks to be available
        while self.is_active:
            if self.chunks:
                return self.chunks.pop(0)
            # Small sleep to prevent busy-waiting
            import time
            time.sleep(0.01)

        # Stream is closed and no more chunks
        if not self.chunks:
            raise StopIteration
        return self.chunks.pop(0)


@router.websocket("/transcribe")
async def websocket_transcription(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription.

    Protocol:
    - Client connects and sends audio chunks as binary data
    - Server transcribes and sends back JSON messages:
      - {"type": "partial", "text": "..."}  - Partial transcripts
      - {"type": "final", "text": "..."}    - Final transcripts
      - {"type": "error", "message": "..."}  - Errors
    - Client can send special control messages as JSON:
      - {"type": "stop"} - Stop transcription
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted for transcription")

    # Create audio stream buffer
    audio_buffer = AudioStreamBuffer()
    transcription_task: Optional[asyncio.Task] = None

    try:
        # Initialize Speechmatics service
        speechmatics_service = SpeechmaticsService()

        # Define callback for partial transcripts
        async def on_partial_transcript(text: str, is_final: bool = False):
            """Send partial transcript to client."""
            try:
                await websocket.send_json({
                    "type": "partial",
                    "text": text,
                    "is_final": False
                })
            except Exception as e:
                logger.error(f"Error sending partial transcript: {e}")

        # Define callback for final transcripts
        async def on_final_transcript(text: str, is_final: bool = True):
            """Send final transcript to client."""
            try:
                await websocket.send_json({
                    "type": "final",
                    "text": text,
                    "is_final": True
                })
            except Exception as e:
                logger.error(f"Error sending final transcript: {e}")

        # Define callback for errors
        async def on_error(error_message: str):
            """Send error to client."""
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": error_message
                })
            except Exception as e:
                logger.error(f"Error sending error message: {e}")

        # Start transcription in a background task
        transcription_task = asyncio.create_task(
            speechmatics_service.start_transcription(
                audio_stream=audio_buffer,
                on_partial=on_partial_transcript,
                on_final=on_final_transcript,
                on_error=on_error,
                enable_partials=True,
                max_delay=1.0,
                operating_point="enhanced"
            )
        )

        # Main loop: receive audio chunks from client
        while True:
            try:
                # Receive message from client
                message = await websocket.receive()

                # Handle binary audio data
                if "bytes" in message:
                    audio_chunk = message["bytes"]
                    logger.debug(f"Received audio chunk: {len(audio_chunk)} bytes")
                    await audio_buffer.add_chunk(audio_chunk)

                # Handle text/JSON control messages
                elif "text" in message:
                    try:
                        control_msg = json.loads(message["text"])
                        if control_msg.get("type") == "stop":
                            logger.info("Stop command received from client")
                            break
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON control message: {message['text']}")

            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                await on_error(f"Error processing audio: {str(e)}")
                break

    except Exception as e:
        logger.error(f"Error in transcription WebSocket: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Transcription error: {str(e)}"
            })
        except:
            pass

    finally:
        # Clean up
        logger.info("Cleaning up transcription WebSocket")
        await audio_buffer.close()

        # Cancel transcription task if running
        if transcription_task and not transcription_task.done():
            transcription_task.cancel()
            try:
                await transcription_task
            except asyncio.CancelledError:
                logger.info("Transcription task cancelled")

        try:
            await websocket.close()
        except:
            pass

        logger.info("WebSocket connection closed")