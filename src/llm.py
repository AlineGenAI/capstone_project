"""Single place where the LLM client is created. Reads settings from the environment."""
import os
from collections.abc import Mapping

from dotenv import load_dotenv
from openai import APIStatusError, OpenAI

load_dotenv()  # loads .env if present; harmless if not

# Course proxy defaults (not secrets). Only LLM_API_KEY is personal to your group.
DEFAULT_BASE_URL = "https://llm-proxy-obfzuamujq-ew.a.run.app/v1"
DEFAULT_MODEL = "course-chat"


class ContentPolicyViolationError(RuntimeError):
    """The LLM provider rejected a request because of a content policy."""


def _contains_content_filter_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        if value.get("code") == "content_filter":
            return True
        return any(_contains_content_filter_marker(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_content_filter_marker(item) for item in value)
    return False


def _is_content_policy_violation(error: APIStatusError) -> bool:
    if error.code == "content_filter":
        return True
    return _contains_content_filter_marker(error.body)


def get_client() -> OpenAI:
    base_url = os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY not set. Check your .env file.")
    return OpenAI(base_url=base_url, api_key=api_key)


def ask(prompt: str, system: str | None = None) -> str:
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    try:
        response = get_client().chat.completions.create(
            model=os.environ.get("LLM_MODEL") or DEFAULT_MODEL, messages=messages
        )
    except APIStatusError as error:
        if error.status_code == 400 and _is_content_policy_violation(error):
            raise ContentPolicyViolationError(
                "The LLM provider blocked this ticket due to its content policy."
            ) from error
        raise
    return response.choices[0].message.content
