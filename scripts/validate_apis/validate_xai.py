#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_post, missing_credentials, status_from_response


PROVIDER = "xai_x_search"


def main() -> int:
    key_name, api_key = get_secret("GROK_API_KEY", "XAI_API_KEY")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["GROK_API_KEY"],
            [
                "Create or use an xAI/Grok API key",
                "Set it with: export GROK_API_KEY='your_key'",
                "Or add GROK_API_KEY=your_key to ~/.secrets",
                "XAI_API_KEY is also accepted as a fallback alias.",
            ],
        )

    response = http_post(
        "https://api.x.ai/v1/responses",
        headers={"Authorization": f"Bearer {api_key}"},
        data={"model": "grok-4.3", "input": [{"role": "user", "content": "Reply with OK."}]},
        timeout=45,
    )
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "docs": "https://docs.x.ai/developers/tools/x-search",
        "cost_note": "xAI/Grok calls can incur model/tool usage costs. Use as cited discovery, not source of record.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
