#!/usr/bin/env python3
"""Very simple LangChain ChatOpenAI example for AmSC LiteLLM.

Usage:
  pip install langchain-openai
  export CBORG_API_KEY="<your_key>"
  python test_langchain_chatopenai.py

Optional environment variables:
  CBORG_BASE_URL (default: https://api.i2-core.american-science-cloud.org/v1)
  CBORG_MODEL    (default: claude-haiku)
  CBORG_USER_AGENT (default: amsc-lc-test/1.0)
"""

import os

from langchain_openai import ChatOpenAI
from openai import PermissionDeniedError


def main() -> None:
    base_url = os.getenv("CBORG_BASE_URL", "https://api.i2-core.american-science-cloud.org")
    api_key = os.getenv("CBORG_API_KEY", "")
    model = os.getenv("CBORG_MODEL", "gpt-oss-120b")
    user_agent = os.getenv("CBORG_USER_AGENT", "amsc-lc-test/1.0")

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0,
        #default_headers={
        #    "User-Agent": user_agent,
        #    "Accept": "application/json",
        #},
    )

    try:
        reply = llm.invoke("Say exactly: LangChain ChatOpenAI test OK")
        print(reply.content)
    except PermissionDeniedError as exc:
        print(f"PermissionDeniedError: {exc}")
        print(
            "Hint: This endpoint may block some SDK User-Agents at Cloudflare.\n"
            "Try setting CBORG_USER_AGENT to a custom value and retry."
        )
        raise


if __name__ == "__main__":
    main()
