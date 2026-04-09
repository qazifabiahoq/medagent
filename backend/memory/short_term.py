import json
import redis.asyncio as redis
import os
from typing import Optional

SESSION_TTL = 60 * 60 * 6  # 6 hours


class ShortTermMemory:
    def __init__(self):
        self.client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

    async def set(self, thread_id: str, key: str, value: any):
        redis_key = f"session:{thread_id}:{key}"
        await self.client.setex(redis_key, SESSION_TTL, json.dumps(value))

    async def get(self, thread_id: str, key: str) -> Optional[any]:
        redis_key = f"session:{thread_id}:{key}"
        data = await self.client.get(redis_key)
        return json.loads(data) if data else None

    async def set_working_memory(self, thread_id: str, state: dict):
        redis_key = f"working:{thread_id}"
        await self.client.setex(redis_key, SESSION_TTL, json.dumps(state, default=str))

    async def get_working_memory(self, thread_id: str) -> Optional[dict]:
        redis_key = f"working:{thread_id}"
        data = await self.client.get(redis_key)
        return json.loads(data) if data else None

    async def clear_session(self, thread_id: str):
        pattern = f"session:{thread_id}:*"
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)
        await self.client.delete(f"working:{thread_id}")

    async def close(self):
        await self.client.aclose()
