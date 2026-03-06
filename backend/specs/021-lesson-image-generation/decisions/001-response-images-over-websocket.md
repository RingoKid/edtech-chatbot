# ADR-001: Image Delivery via HTTP Response Instead of WebSocket Events

## Status
Accepted

## Context
The original spec called for delivering images via separate WebSocket `image_ready` events after lesson generation. This would allow images to appear asynchronously one-by-one as they generate.

However, the current chat architecture uses a simple request-response pattern (`POST /chat/message` → JSON response). The WebSocket connection (`/ws/message`) exists but is not actively used by the Chatbot2 component — messages go through HTTP.

## Decision
Deliver image data (URLs, placement, alt_text) as part of the HTTP chat response instead of separate WebSocket events.

The `ChatMessageResponse` schema was extended with an optional `images` field:
```python
class ChatMessageResponse(BaseModel):
    thread_id: str
    reply: str
    images: Optional[list[ImageReadyEvent]] = None
```

## Consequences
**Pros:**
- Simpler implementation — no WebSocket event handling needed in frontend
- Images arrive in the same response as the lesson text
- No state synchronization issues between WebSocket and HTTP channels
- Easier to test (just check the JSON response)

**Tradeoffs:**
- Response time is longer when images are generating (includes 10-15s for Gemini API)
- Images don't appear one-by-one (all 3 arrive together)
- If we later want progressive image loading, we'd need to add WebSocket support

**Migration path:**
If progressive image loading becomes important, we can add WebSocket events alongside the HTTP response — the `ImageReadyEvent` schema is already defined and can be reused.
