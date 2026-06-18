from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import Any


class QueueBackend(ABC):
    runs_inline: bool = True

    @abstractmethod
    async def create_job(self, job: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def update_job(self, job_id: str, **fields: Any) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def list_jobs(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def reserve_job(self, *, timeout: int = 5) -> dict[str, Any] | None:
        return None

    async def close(self) -> None:
        return None


class MemoryQueueBackend(QueueBackend):
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}

    async def create_job(self, job: dict[str, Any]) -> dict[str, Any]:
        self.jobs[job["id"]] = job
        return job

    async def update_job(self, job_id: str, **fields: Any) -> dict[str, Any]:
        self.jobs[job_id].update(fields)
        return self.jobs[job_id]

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    async def list_jobs(self) -> list[dict[str, Any]]:
        return list(self.jobs.values())


class RedisQueueBackend(QueueBackend):
    runs_inline = False

    def __init__(self, redis_url: str, *, prefix: str = "tg-api-zapret") -> None:
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis = None

    async def create_job(self, job: dict[str, Any]) -> dict[str, Any]:
        redis = await self._client()
        await redis.sadd(self._index_key(), job["id"])
        await redis.set(self._job_key(job["id"]), json.dumps(job, ensure_ascii=False))
        await redis.rpush(self._queue_key(), job["id"])
        return job

    async def update_job(self, job_id: str, **fields: Any) -> dict[str, Any]:
        job = await self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        job.update(fields)
        redis = await self._client()
        await redis.set(self._job_key(job_id), json.dumps(job, ensure_ascii=False))
        return job

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        redis = await self._client()
        value = await redis.get(self._job_key(job_id))
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(value)

    async def list_jobs(self) -> list[dict[str, Any]]:
        redis = await self._client()
        job_ids = await redis.smembers(self._index_key())
        jobs = []
        for job_id in sorted(decode_redis_value(item) for item in job_ids):
            job = await self.get_job(job_id)
            if job is not None:
                jobs.append(job)
        return jobs

    async def reserve_job(self, *, timeout: int = 5) -> dict[str, Any] | None:
        redis = await self._client()
        item = await redis.blpop(self._queue_key(), timeout=timeout)
        if item is None:
            return None
        _, job_id = item
        return await self.get_job(decode_redis_value(job_id))

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def _client(self):
        if self._redis is None:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(self.redis_url, decode_responses=False)
        return self._redis

    def _job_key(self, job_id: str) -> str:
        return f"{self.prefix}:job:{job_id}"

    def _index_key(self) -> str:
        return f"{self.prefix}:jobs"

    def _queue_key(self) -> str:
        return f"{self.prefix}:queue"


def build_queue_backend(kind: str = "memory", *, redis_url: str | None = None) -> QueueBackend:
    if kind == "memory":
        return MemoryQueueBackend()
    if kind == "redis":
        if not redis_url:
            raise ValueError("redis_url is required for Redis queue backend")
        return RedisQueueBackend(redis_url)
    raise ValueError(f"Unsupported queue backend: {kind}")


def decode_redis_value(value: str | bytes) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else value
