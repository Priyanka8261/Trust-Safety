from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

# Load .env file from project root (optional fallback)
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

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
    
    Args:
        api_key: OpenAI API key (if None, tries to read from environment)
        temperature: Model temperature (default: 0.0)
        model: Model name (default: gpt-4o-mini)
    
    Returns:
        ChatOpenAI client instance
    """
    # Use provided API key, or try to get from environment
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OpenAI API key is required. "
            "Please provide it in the UI or set OPENAI_API_KEY in your .env file."
        )
    
    # Create ChatOpenAI client with the provided API key
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)


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
    # Fallback minimal schema
    return {"category": "SAFE", "explanation": "Unable to parse model JSON; defaulted to SAFE."}


def _normalize_result(obj: Dict[str, Any]) -> Dict[str, str]:
    """
    Ensure required keys exist and normalize category to allowed set.
    """
    category = str(obj.get("category", "")).strip().upper()
    explanation = str(obj.get("explanation", "")).strip()
    if category not in CATEGORIES:
        # crude mapping from common lower-case labels
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
    """
    Classify dating-profile text into one of the categories with a short explanation.

    Parameters
    ----------
    text : str
        The input text to classify.
    api_key : Optional[str]
        OpenAI API key. If not provided, tries to read from environment.
    model : str
        OpenAI model to use (default: gpt-4o-mini).
    llm : Optional[BaseChatModel]
        Optional injected LLM (for testing). If provided, api_key and model are ignored.

    Returns
    -------
    Dict[str, str]
        { "category": <SAFE|MANIPULATIVE|UNSAFE|OBJECTIFYING>, "explanation": <str> }
    """
    if not isinstance(text, str) or not text.strip():
        return {"category": "SAFE", "explanation": "Empty input text."}

    # Use provided LLM or create one with the API key
    if llm is None:
        client = _get_llm(api_key=api_key, temperature=0.0, model=model)
    else:
        client = llm
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text.strip()),
    ]
    try:
        resp = client.invoke(messages)
        raw = resp.content if hasattr(resp, "content") else str(resp)
    except Exception as e:
        return {
            "category": "SAFE",
            "explanation": f"Model call failed: {e}",
        }

    result = _extract_json(raw)
    return _normalize_result(result)

