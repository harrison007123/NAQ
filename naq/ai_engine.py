import re
from typing import Optional
import requests
from rich.console import Console
from naq import db

console = Console()

GROQ_MODELS = [
    {
        "label": "1) openai/gpt-oss-120b   (reasoning — medium effort)",
        "model": "openai/gpt-oss-120b",
        "variant": "reasoning",
    },
    {
        "label": "2) groq/compound          (compound with web/code tools)",
        "model": "groq/compound",
        "variant": "compound",
    },
    {
        "label": "3) llama-3.1-8b-instant   (fast, standard chat)",
        "model": "llama-3.1-8b-instant",
        "variant": "standard",
    },
]

_THINKING_MODEL_KEYWORDS = ("qwen3", "deepseek-r1", "r1-", "thinking", "gpt-oss")
def log(message):
    with open("output.log", "w") as f:
        f.write(message + "\n")

USER_PROMPT_TEMPLATE = """Database schema:
{schema}

User question:
{question}

Return only the SQL query."""

def _build_system_prompt(db_type: str) -> str:
    dialect_map = {"mysql": "MySQL", "postgresql": "PostgreSQL"}
    dialect = dialect_map.get(db_type.lower(), db_type.upper())
    type_hints = {
        "mysql": (
            "Use MySQL-compatible data types ONLY: "
            "INT or BIGINT (not NUMBER), VARCHAR(n) (not VARCHAR2), "
            "TEXT, FLOAT, DOUBLE, DECIMAL, DATE, DATETIME, BOOLEAN."
        ),
        "postgresql": (
            "Use PostgreSQL-compatible data types ONLY: "
            "INTEGER or BIGINT (not NUMBER), VARCHAR(n) or TEXT (not VARCHAR2), "
            "NUMERIC, REAL, DOUBLE PRECISION, DATE, TIMESTAMP, BOOLEAN."
        ),
    }
    hint = type_hints.get(db_type.lower(), "")
    return f"""You are an expert SQL engineer.

Target database dialect: {dialect}

You will receive a natural language request from the user.

Your task is to generate a valid SQL query that fulfills the request.



Rules:
- Return ONLY the raw SQL query. No explanations, comments, or markdown.
- Use ONLY tables and columns present in the given schema.
- Do NOT assume or hallucinate any table or column names.
- Determine the correct SQL operation (SELECT, INSERT, UPDATE, DELETE) based on user intent.
- Prefer SELECT queries unless the user explicitly requests data modification.
- Use proper JOINs when multiple tables are involved.
- Apply filtering (WHERE), grouping (GROUP BY), aggregation (COUNT, SUM, etc.), and ordering (ORDER BY) when appropriate.
- Ensure the query is syntactically correct for {dialect}.
 
IMPORTANT NOTE:
 - Don't use any previous history always use fresh generation, use correct words given as per the users


"""


def _clean_sql(raw: str) -> str:
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw)
    return raw.strip()


def _is_thinking_model(model: str) -> bool:
    return any(kw in model.lower() for kw in _THINKING_MODEL_KEYWORDS)


def _get_groq_variant(model_id: str) -> str:
    for m in GROQ_MODELS:
        if m["model"] == model_id:
            return m["variant"]
    if _is_thinking_model(model_id):
        return "reasoning"
    if "compound" in model_id:
        return "compound"
    return "standard"

def _call_groq(api_key: str, model: str, schema: str, question: str, db_type: str = "mysql") -> str:
    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("The `groq` package is not installed. Run: pip install groq")

    client = Groq(api_key=api_key)
    user_content = USER_PROMPT_TEMPLATE.format(schema=schema, question=question)
    variant = _get_groq_variant(model)
    system_prompt = _build_system_prompt(db_type)
    combined = system_prompt + "\n\n"+'''
Below is the schema for all the table

'''+user_content

    if variant == "reasoning":
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": combined}],
            temperature=1,
            max_completion_tokens=8192,
            top_p=1,
            reasoning_effort="medium",
            stream=False,
            stop=None,
        )
    elif variant == "compound":
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": combined},
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
            compound_custom={"tools": {"enabled_tools": ["web_search", "code_interpreter", "visit_website"]}},
        )
    else:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": combined},
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

    content = completion.choices[0].message.content or ""
    return _clean_sql(content)


def _raise_api_error(provider: str, response) -> None:
    status = response.status_code
    try:
        body = response.json()
        msg = body.get("error", {}).get("message") or response.text
    except Exception:
        msg = response.text or "(no response body)"
    raise RuntimeError(f"{provider} API error (HTTP {status}): {msg}")


def _call_openai(api_key: str, model: str, schema: str, question: str, db_type: str = "mysql") -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _build_system_prompt(db_type)},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(schema=schema, question=question)},
        ],
        "temperature": 0,
        "max_tokens": 1024,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    if not response.ok:
        _raise_api_error("OpenAI", response)
    return _clean_sql(response.json()["choices"][0]["message"]["content"])


def generate_sql(cfg: dict, schema_text: str, question: str) -> str:
    llm_cfg = cfg["llm"]
    provider = llm_cfg["provider"].lower()
    api_key = llm_cfg["api_key"]
    model = llm_cfg["model"]
    db_type = cfg.get("database", {}).get("type", "mysql")

    try:
        if provider == "openai":
            return _call_openai(api_key, model, schema_text, question, db_type)
        elif provider == "groq":
            return _call_groq(api_key, model, schema_text, question, db_type)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"LLM call failed: {exc}") from exc
