import asyncio, base64
import httpx
from app.config import settings

class JudgeUnavailable(RuntimeError): pass

class Judge0Service:
    language_id = 62
    def __init__(self):
        self.headers = {"X-Auth-Token": settings.judge0_api_key} if settings.judge0_api_key else {}

    async def evaluate(self, source: str, cases: list[dict]) -> dict:
        results, total_time, max_memory = [], 0.0, 0
        async with httpx.AsyncClient(base_url=settings.judge0_base_url, timeout=settings.request_timeout_seconds, headers=self.headers) as client:
            for case in cases:
                try:
                    response = await client.post("/submissions?base64_encoded=true&wait=false", json={
                        "language_id": self.language_id,
                        "source_code": _b64(source), "stdin": _b64(str(case.get("input", ""))),
                        "expected_output": _b64(str(case.get("expected", ""))),
                        "cpu_time_limit": 3,
                        "memory_limit": 1536000,
                        "enable_per_process_and_thread_time_limit": True,
                        "enable_per_process_and_thread_memory_limit": True,
                    })
                    response.raise_for_status(); token = response.json()["token"]
                    data = await self._poll(client, token)
                except (httpx.HTTPError, KeyError) as exc:
                    raise JudgeUnavailable(f"Judge0 is unavailable: {exc}") from exc
                status = data.get("status", {}).get("id", 0)
                passed = status == 3
                runtime = float(data.get("time") or 0) * 1000
                memory = int(data.get("memory") or 0)
                total_time += runtime; max_memory = max(max_memory, memory)
                results.append({"passed": passed, "status": data.get("status", {}).get("description", "Unknown"), "input": case.get("input") if case.get("visible") else None})
                if status in {6, 7, 8, 9, 10, 11, 12, 13, 14}:
                    return {"correct": False, "results": results, "compiler_output": _decode(data.get("compile_output") or data.get("stderr") or data.get("message")), "runtime_ms": total_time, "memory_kb": max_memory}
        return {"correct": all(r["passed"] for r in results), "results": results, "compiler_output": None, "runtime_ms": total_time, "memory_kb": max_memory}

    async def _poll(self, client, token):
        for delay in [0.1, .2, .4, .8, 1, 1, 1]:
            await asyncio.sleep(delay)
            response = await client.get(f"/submissions/{token}?base64_encoded=true&fields=status,time,memory,compile_output,stderr,message")
            response.raise_for_status(); data = response.json()
            if data.get("status", {}).get("id", 0) > 2: return data
        raise JudgeUnavailable("Judge0 submission timed out")

def _b64(value): return base64.b64encode(value.encode()).decode()
def _decode(value):
    if not value: return None
    try: return base64.b64decode(value).decode(errors="replace")
    except Exception: return str(value)
