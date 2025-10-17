"""
Self-contained mock test that simulates ChatService.handle_message behavior without importing project modules.
This avoids installing backend dependencies and verifies the request/response shape quickly.
"""

import asyncio
import json


class FakeChatService:
    def __init__(self):
        pass

    def create_new_thread(self, user_id: str) -> str:
        return f"{user_id}_mockthread"

    async def handle_message(self, user_message: str, user_id: str, thread_id: str | None = None):
        if thread_id is None:
            thread_id = self.create_new_thread(user_id)

        # Simulate async processing
        await asyncio.sleep(0)
        reply = f"Echo: {user_message}"
        return {"reply": reply, "thread_id": thread_id}


async def run_test():
    svc = FakeChatService()
    res = await svc.handle_message("hello test", user_id="tester", thread_id=None)
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    asyncio.run(run_test())
