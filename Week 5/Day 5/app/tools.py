import concurrent.futures
import logging
from pathlib import Path
from .config import settings
from .db import get_service

logger = logging.getLogger("agent.tools")

class ToolError(RuntimeError):
    pass

def _run_with_timeout(fn, *args):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args)
        try:
            return future.result(timeout=settings.tool_timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            raise ToolError(f"Tool timed out after {settings.tool_timeout_seconds}s") from exc
        except Exception as exc:
            raise ToolError(str(exc)) from exc

def load_company_profile() -> str:
    def read_profile():
        return Path(settings.company_profile_path).read_text(encoding="utf-8")
    result = _run_with_timeout(read_profile)
    logger.info("company profile loaded", extra={"event": "tool_call"})
    return result

def lookup_service(project_type: str) -> dict:
    result = _run_with_timeout(get_service, project_type)
    logger.info("service catalog queried", extra={"event": "tool_call"})
    return result
