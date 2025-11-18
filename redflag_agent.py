from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

# Guard dotenv import so missing python-dotenv won't crash production
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

from pathlib import Path

# LangChain monolith imports (compatible with `langchain` in requirements)
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

BaseChatModel = Any

# Load .env from project root only if python-dotenv is available
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
if env_path.exists() and load_dotenv is not None:
    try:
        load_dotenv(dotenv_path=env_path, override=True)
    except Exception:
        pass  # continue if dotenv fails

CATEGORIES = ["SAFE", "MANIPULATIVE", "UNSAFE", "OBJECTIFYING"]

SYSTEM_PROMPT = (
    "You are a Trust & Safety classifier for dating-profile text. "
    "Classify input into exactly one category and return STRICT JSON only.\n\n"
    "Categories:\n"
    "- SAFE: respectful/consent-aware.\n"
    "- MANIPULATIVE: guilt-tripping, controlling, pressuring, negging.\n"
    "- UNSAFE: sexual solicitation, harassment, coercion, doxxing hints.\n"
    "- OBJECTIFYING: reducing people to looks, body parts, money/status.\n\n"
    "Output JSON schema:\n"
    "{\n"
    '  \"category\": \"SAFE|MANIPULATIVE|UNSAFE|OBJECTIFYING\",\n'
    '  \"explanation\": \"short, plain-language reason\"\n'
    "}\n"
    "Rules:\n"
    "- Temperature is zero: be deterministic and concise.\n"
    "- Do not include any text before or after the JSON.\n"
)


def _get_llm(api_key: Optional[str] = None, temperature: float = 0.0, model: str = "gpt-4o-mini") -> BaseChatModel:
    """
    Create a ChatOpenAI client. Uses provided API key or falls back to environment.
    """
    # prefer explicit api_key, then environment variable, then st.secrets at runtime
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY in environment or in Streamlit secrets."
        )

    # ChatOpenAI in langchain typically accepts openai_api_key (varies by version)
    # We pass openai_api_key to be compatible with most langchain versions
    return ChatOpenAI(model=model, temperature=temperature, openai_api_key=api_key)


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Try to parse strict JSON; if it fails, attempt to extract the first JSON object via regex.
    """
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*?\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {"category": "SAFE", "explanation": "Unable to parse model JSON; defaulted to SAFE."}


def _normalize_result(obj: Dict[str, Any]) -> Dict[str, str]:
    category = str(obj.get("category", "")).strip().upper()
    explanation = str(obj.get("explanation", "")).strip()
    if category not in CATEGORIES:
        mapping = {
            "safe": "SAFE",
            "manipulative": "MANIPULATIVE",
            "unsafe": "UNSAFE",
            "objectifying": "OBJECTIFYING",
        }
        category = mapping.get(category.lower(), "SAFE")
    if not explanation:
        explanation = "Classification produced without a detailed explanation."
    return {"category": category, "explanation": explanation}


def classify_prompt(
    text: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    llm: Optional[BaseChatModel] = None
) -> Dict[str, str]:
    if not isinstance(text, str) or not text.strip():
        return {"category": "SAFE", "explanation": "Empty input text."}

    if llm is None:
        client = _get_llm(api_key=api_key, temperature=0.0, model=model)
    else:
        client = llm

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text.strip()),
    ]

    try:
        # Many langchain ChatOpenAI clients are callable or implement .generate/.__call__
        if callable(client):
            resp = client(messages)
        else:
            # Fallback: try generate, then __call__
            try:
                resp = client.generate(messages)
            except Exception:
                resp = client.__call__(messages)
        # Normalize several possible response shapes:
        if isinstance(resp, str):
            raw = resp
        elif hasattr(resp, "generations"):
            # typical shape: resp.generations[0][0].text
            try:
                raw = resp.generations[0][0].text
            except Exception:
                raw = str(resp)
        elif hasattr(resp, "content"):
            raw = resp.content
        else:
            raw = str(resp)
    except Exception as e:
        return {"category": "SAFE", "explanation": f"Model call failed: {e}"}

    result = _extract_json(raw)
    return _normalize_result(result)

