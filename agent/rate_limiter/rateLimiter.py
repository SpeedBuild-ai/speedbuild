import time
import asyncio
from typing import Any


class LLMRateLimiter:
    def __init__(
        self,
        max_retries: int = 5,
        consecutive_limit_threshold: int = 5,
        cooldown_seconds: float = 60.0,
    ):
        self.max_retries = max_retries

        # cooldown state
        self.consecutive_limit_threshold = consecutive_limit_threshold
        self.cooldown_seconds = cooldown_seconds

        self._consecutive_rate_limits = 0
        self._cooldown_until: float | None = None
        self._lock = asyncio.Lock()

    async def call(self, llm, **kwargs) -> Any:
        retries = 0

        while True:
            # Global cooldown gate
            await self._maybe_cooldown()

            try:
                result = await llm.ainvoke(**kwargs)

                # success resets counters
                async with self._lock:
                    self._consecutive_rate_limits = 0

                return result

            except Exception as e:
                if not self._is_rate_limit(e):
                    raise  # real error, don't swallow it

                retries += 1

                async with self._lock:
                    self._consecutive_rate_limits += 1

                    # Trigger cooldown if threshold exceeded
                    if self._consecutive_rate_limits >= self.consecutive_limit_threshold:
                        self._cooldown_until = time.monotonic() + self.cooldown_seconds
                        self._consecutive_rate_limits = 0
                        print(
                            f"[rate-limit] cooldown triggered "
                            f"({self.cooldown_seconds:.0f}s)"
                        )

                if retries > self.max_retries:
                    raise RuntimeError("Exceeded max retries due to rate limits")

                wait_time = self._get_retry_after(e, retries)
                print(f"[rate-limit] waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

    async def _maybe_cooldown(self):
        async with self._lock:
            if self._cooldown_until is None:
                return

            remaining = self._cooldown_until - time.monotonic()
            if remaining > 0:
                print(f"[rate-limit] cooling down for {remaining:.2f}s")
            else:
                self._cooldown_until = None
                return

        # sleep outside lock
        await asyncio.sleep(remaining)

    def _is_rate_limit(self, e: Exception) -> bool:
        msg = str(e).lower()
        return (
            "rate limit" in msg
            or "tpm" in msg
            or "429" in msg
        )

    def _get_retry_after(self, e: Exception, retries: int) -> float:
        # Respect Retry-After if provided
        if hasattr(e, "headers") and "Retry-After" in e.headers:
            try:
                return float(e.headers["Retry-After"])
            except ValueError:
                pass

        # Exponential backoff + small jitter
        base = min(60.0, 2 ** retries)
        jitter = 0.1 * retries
        return base + jitter
