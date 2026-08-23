"""In-memory background-job registry for ML predictions.

Training takes seconds-to-tens-of-seconds, so predict runs as a background
task: POST creates a job, GET polls it. Results are also pushed to the Redis
cache by the service layer so repeat requests are instant. When a real worker
(arq) arrives in a later phase this registry becomes the worker's queue —
the HTTP contract stays identical.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

_jobs: dict[str, dict[str, Any]] = {}
_job_futures: dict[str, asyncio.Task] = {}


def create_job(symbol: str, coro) -> str:
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {
        "job_id": job_id,
        "symbol": symbol,
        "status": "running",
        "started_at": time.time(),
        "finished_at": None,
        "result": None,
        "error": None,
    }
    _job_futures[job_id] = asyncio.create_task(_run(job_id, coro))
    return job_id


async def _run(job_id: str, coro) -> None:
    try:
        result = await coro
        _jobs[job_id]["result"] = result
        _jobs[job_id]["status"] = "done"
    except Exception as exc:  # noqa: BLE001 - surfaced through the job payload
        _jobs[job_id]["error"] = str(exc)
        _jobs[job_id]["status"] = "error"
    finally:
        _jobs[job_id]["finished_at"] = time.time()
        _job_futures.pop(job_id, None)


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)
