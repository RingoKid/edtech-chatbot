"""
WebSocket endpoint for real-time audio transcription using Speechmatics.
Frontend sends audio chunks, backend transcribes and sends back text.
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.speechmatics_service import SpeechmaticsService
from app.dependencies.auth import get_websocket_user
from app.schemas.auth import UserInDB
import json
import io

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


class AudioStreamBuffer:
    """
    Buffer for collecting audio chunks from WebSocket and providing them
    to the Speechmatics service as a file-like object.
    """

    def __init__(self):
        self.chunks = []
        self.is_active = True
        self.lock = asyncio.Lock()
        self.current_chunk = b''
        self.position = 0

    async def add_chunk(self, chunk: bytes):
        """Add an audio chunk to the buffer."""
        async with self.lock:
            if self.is_active:
                self.chunks.append(chunk)

    async def close(self):
        """Close the stream."""
        async with self.lock:
            self.is_active = False

    def read(self, size: int = -1):
        """
        Read bytes from the buffer.
        This method makes the buffer compatible with Speechmatics SDK's expectations.
        """
        import time

        # Wait for data to be available
        # Keep waiting while stream is active and no chunks available
        while self.is_active and not self.chunks:
            time.sleep(0.01)  # 10ms sleep to prevent busy-waiting

        # Get chunk from buffer if available
        if self.chunks:
            try:
                chunk = self.chunks.pop(0)

                # If size is specified, return only that amount
                if size > 0 and len(chunk) > size:
                    # Split chunk and put remainder back
                    self.chunks.insert(0, chunk[size:])
                    return chunk[:size]

                return chunk
            except IndexError:
                # Race condition - chunk was removed
                # Continue waiting for more chunks
                return self.read(size)

        # If stream is closed and no chunks, return empty bytes to signal EOF
        if not self.is_active:
            return b''

        # Should not reach here, but return empty if we do
        return b''

    def __iter__(self):
        """Make the buffer iterable for Speechmatics SDK."""
        return self

    def __next__(self):
        """
        Get the next chunk synchronously.
        This is required by Speechmatics SDK which expects a synchronous iterator.
        """
        chunk = self.read()
        if not chunk and not self.is_active:
            raise StopIteration
        return chunk


@router.websocket("/transcribe")
async def websocket_transcription(
    websocket: WebSocket,
    user: Optional[UserInDB] = Depends(get_websocket_user)
):
    """
    WebSocket endpoint for real-time audio transcription.

    Protocol:
    - Client connects with token query param: ws://...?token=<jwt>
    - Client sends audio chunks as binary data
    - Server transcribes and sends back JSON messages:
      - {"type": "partial", "text": "..."}  - Partial transcripts
      - {"type": "final", "text": "..."}    - Final transcripts
      - {"type": "error", "message": "..."}  - Errors
    - Client can send special control messages as JSON:
      - {"type": "stop"} - Stop transcription
    """
    # Validate authentication
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning("WebSocket connection rejected: no valid token")
        return

    await websocket.accept()
    logger.info(f"WebSocket connection accepted for transcription (user: {user.user_id})")

    # Create audio stream buffer
    audio_buffer = AudioStreamBuffer()
    transcription_task: Optional[asyncio.Task] = None
    ws_active = True

    try:
        # Initialize Speechmatics service
        logger.info("Initializing Speechmatics service...")
        speechmatics_service = SpeechmaticsService()
        logger.info("Speechmatics service initialized successfully")

        # Define callback for partial transcripts
        async def on_partial_transcript(text: str, is_final: bool = False):
            """Send partial transcript to client."""
            if not ws_active:
                return
            try:
                await websocket.send_json({
                    "type": "partial",
                    "text": text,
                    "is_final": False
                })
            except Exception as send_error:
                logger.error(f"Error sending partial transcript: {send_error}")

        # Define callback for final transcripts
        async def on_final_transcript(text: str, is_final: bool = True):
            """Send final transcript to client."""
            if not ws_active:
                return
            try:
                await websocket.send_json({
                    "type": "final",
                    "text": text,
                    "is_final": True
                })
            except Exception as send_error:
                logger.error(f"Error sending final transcript: {send_error}")

        # Define callback for errors
        async def on_error(error_message: str):
            """Send error to client."""
            if not ws_active:
                return
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": error_message
                })
            except Exception as send_error:
                logger.error(f"Error sending error message: {send_error}")

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
                ws_active = False
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                await on_error(f"Error processing audio: {str(e)}")
                ws_active = False
                break

    except Exception as e:
        logger.error(f"Error in transcription WebSocket: {e}")
        if ws_active:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Transcription error: {str(e)}"
                })
            except:
                pass
        ws_active = False

    finally:
        # Mark WebSocket as inactive to stop callbacks
        ws_active = False

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