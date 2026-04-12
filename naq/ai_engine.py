import ast
import json
import re
from typing import List, Optional
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
    with open("output.log", "a") as f:
        f.write(message + "\n")

USER_PROMPT_TEMPLATE = """Database schema:
{schema}

User question:
{question}

Return the SQL as a JSON array of strings. Each element must be one complete SQL statement.

Example for a simple SELECT:
["SELECT * FROM users"]

Example for a trigger:
["DROP TRIGGER IF EXISTS before_insert_users", "CREATE TRIGGER before_insert_users BEFORE INSERT ON users FOR EACH ROW BEGIN SET NEW.name = UPPER(NEW.name); END"]

IMPORTANT:
- Return ONLY the JSON array. No markdown, no explanation, no extra text.
- Each string in the array must be a complete, standalone SQL statement.
- For triggers: keep the entire CREATE TRIGGER ... BEGIN ... END as ONE single string in the array.
- Semicolons INSIDE a BEGIN...END block are part of the trigger body — keep them inside the string.
- Use double quotes for all strings in the JSON array.
"""

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

Your task is to generate valid SQL statements that fulfill the request.

You MUST return your answer as a JSON array of strings, where each string is one complete SQL statement.

Rules:
- Return ONLY the JSON array of SQL strings. No explanations, comments, or markdown.
- Use ONLY tables and columns present in the given schema.
- Do NOT assume or hallucinate any table or column names.
- Determine the correct SQL operation (SELECT, INSERT, UPDATE, DELETE, CREATE TRIGGER, etc.) based on user intent.
- Prefer SELECT queries unless the user explicitly requests data modification.
- Use proper JOINs when multiple tables are involved.
- Apply filtering (WHERE), grouping (GROUP BY), aggregation (COUNT, SUM, etc.), and ordering (ORDER BY) when appropriate.
- Ensure each query is syntactically correct for {dialect}.
- For triggers: include a DROP TRIGGER IF EXISTS as the first element, followed by the full CREATE TRIGGER statement as the second element. Keep the entire BEGIN...END block inside one string. Ensure EVERY statement inside the BEGIN...END block is properly terminated with a semicolon (;).
- For single queries, return an array with one element.

IMPORTANT NOTE:
 - Don't use any previous history always use fresh generation, use correct words given as per the users
 - ALWAYS return a JSON array, even for a single query: ["SELECT ..."]

"""


def _clean_response(raw: str) -> str:
    """Remove thinking tags and markdown fences from the LLM response."""
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```(?:python|sql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw)
    return raw.strip()


def _parse_query_list(raw: str) -> List[str]:
    """
    Parse the LLM response into a list of SQL query strings.
    The LLM is instructed to return a JSON array of strings.
    Uses json.loads as primary parser, ast.literal_eval as fallback.
    """
    cleaned = _clean_response(raw)
    log(f"=== Cleaned LLM Response ===\n{cleaned}\n=== END ===")

    # Strategy 1: Try json.loads directly on the full cleaned response
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            queries = [str(q).strip() for q in result if str(q).strip()]
            if queries:
                log(f"[PARSE] json.loads direct SUCCESS: {len(queries)} queries")
                for i, q in enumerate(queries):
                    log(f"[PARSE] Query {i+1}: {repr(q[:200])}")
                return queries
    except (json.JSONDecodeError, ValueError) as e:
        log(f"[PARSE] json.loads direct FAILED: {e}")

    # Strategy 2: Extract JSON array from surrounding text using regex
    list_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if list_match:
        matched_text = list_match.group(0)
        log(f"[PARSE] Regex found array pattern, trying json.loads")
        try:
            result = json.loads(matched_text)
            if isinstance(result, list):
                queries = [str(q).strip() for q in result if str(q).strip()]
                if queries:
                    log(f"[PARSE] Regex+json SUCCESS: {len(queries)} queries")
                    return queries
        except (json.JSONDecodeError, ValueError) as e:
            log(f"[PARSE] Regex+json FAILED: {e}")

        # Strategy 3: Try ast.literal_eval as secondary fallback
        try:
            result = ast.literal_eval(matched_text)
            if isinstance(result, list):
                queries = [str(q).strip() for q in result if str(q).strip()]
                if queries:
                    log(f"[PARSE] ast.literal_eval SUCCESS: {len(queries)} queries")
                    return queries
        except (ValueError, SyntaxError) as e:
            log(f"[PARSE] ast.literal_eval FAILED: {e}")

    # Final fallback: treat the whole cleaned response as a single SQL query
    cleaned = re.sub(r"```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned).strip()
    log(f"[PARSE] FALLBACK - treating as single query: {repr(cleaned[:200])}")
    if cleaned:
        return [cleaned]
    return []


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
            max_completion_tokens=4096,
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
    log(f"=== Raw LLM Response ===\n{content}")
    queries = _parse_query_list(content)
    log(f"\n=== Parsed Queries ({len(queries)}) ===")
    for i, q in enumerate(queries):
        log(f"\n--- Query {i+1} ---\n{q}")
    return queries


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
    return _parse_query_list(response.json()["choices"][0]["message"]["content"])


def generate_sql(cfg: dict, schema_text: str, question: str) -> List[str]:
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
