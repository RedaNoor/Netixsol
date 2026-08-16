import logging
import time
from openai import OpenAI
from .config import settings
from .schemas import ClientRequest, ProposalDraft

logger = logging.getLogger("agent.llm")

SYSTEM_PROMPT = """
You are a proposal drafting assistant for a software and AI services agency.
Your output must be suitable for internal review, not direct client delivery.
Use only the supplied company profile, service record, and lead details.
Do not invent services, prices, policies, integrations, facts, or guarantees.
Never promise guaranteed profit, growth, security, legal outcomes, or a fixed result.
If the requested budget or timeline conflicts with the service minimums, state that the
engagement needs discovery/phasing and keep assumptions explicit.
Return only the requested structured proposal fields.
""".strip()

def create_client() -> OpenAI:
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.model_timeout_seconds,
        max_retries=settings.max_model_retries,
        default_headers={
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        },
    )

def create_proposal(req: ClientRequest, service: dict, company_profile: str) -> tuple[ProposalDraft, dict, list[str]]:
    client = create_client()
    user_prompt = f"""
COMPANY PROFILE:
{company_profile}

SERVICE RECORD:
{service}

LEAD DETAILS:
{req.model_dump_json()}

Draft a structured proposal. Respect the service minimum price and minimum timeline.
If the lead's budget/timeline is below the minimum, do not pretend it is feasible; make
that constraint explicit in risks/assumptions/next steps.
""".strip()

    schema = ProposalDraft.model_json_schema()
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1600,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "proposal_draft", "strict": True, "schema": schema},
        },
    )
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    content = response.choices[0].message.content or ""
    proposal = ProposalDraft.model_validate_json(content)
    usage = response.usage
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    cost = (prompt_tokens / 1_000_000 * settings.model_cost_input_per_million) + (completion_tokens / 1_000_000 * settings.model_cost_output_per_million)
    metrics = {
        "model": settings.openrouter_model,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "estimated_cost_usd": round(cost, 8),
    }
    logger.info("OpenRouter model call completed", extra={"event": "model_call", **metrics})
    return proposal, metrics, []
