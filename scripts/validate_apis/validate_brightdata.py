#!/usr/bin/env python3
from __future__ import annotations

import urllib.parse

from common import fields_present, finish, get_secret, http_get, missing_credentials, redact_sensitive, status_from_response


PROVIDER = "brightdata"


def main() -> int:
    selenium_name, selenium_url = get_secret("BRIGHTDATA_SELENIUM_URL", "BRIGHT_DATA_SELENIUM_URL")
    browser_name, browser_ws = get_secret("BRIGHTDATA_BROWSER_WS_URL", "BRIGHT_DATA_BROWSER_WS_URL")
    key_name, token = get_secret("BRIGHTDATA_API_KEY", "BRIGHT_DATA_API_KEY")

    raw = {
        "selenium": None,
        "browser_ws_configured": bool(browser_ws),
        "api_balance": None,
    }
    summaries: dict[str, object] = {
        "selenium_url_configured": bool(selenium_url),
        "browser_ws_url_configured": bool(browser_ws),
        "api_key_configured": bool(token),
    }

    if selenium_url:
        parsed = urllib.parse.urlsplit(selenium_url.rstrip("/"))
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        status_url = urllib.parse.urlunsplit((parsed.scheme, netloc, "/status", "", ""))
        basic_auth = (urllib.parse.unquote(parsed.username), urllib.parse.unquote(parsed.password)) if parsed.username and parsed.password else None
        response = http_get(status_url, basic_auth=basic_auth)
        raw["selenium"] = response
        status = status_from_response(response)
        summary = {
            "status": status,
            "credential_source": selenium_name,
            "http_status": response.get("status_code"),
            "fields": fields_present(response.get("body")),
            **summaries,
            "docs": "https://docs.brightdata.com/scraping-automation/scraping-browser/introduction",
            "cost_note": "Bright Data Browser API / Selenium sessions can incur usage costs. Use low-volume validation before broad collection.",
            "notes": "Validated Selenium Browser API endpoint via /status. WebSocket Browser API URL is treated as configured if present; full Playwright/Puppeteer validation requires a browser client dependency.",
        }
        return finish(PROVIDER, summary, raw)

    if browser_ws:
        parsed = urllib.parse.urlsplit(browser_ws)
        ws_ok = parsed.scheme in {"ws", "wss"} and bool(parsed.hostname)
        raw["browser_ws"] = {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "username_present": bool(parsed.username),
            "password_present": bool(parsed.password),
        }
        summary = {
            "status": "ok" if ws_ok else "failed",
            "credential_source": browser_name,
            "http_status": None,
            "fields": fields_present(raw["browser_ws"]),
            **summaries,
            "docs": "https://docs.brightdata.com/scraping-automation/scraping-browser/introduction",
            "cost_note": "Bright Data Browser API / Playwright sessions can incur usage costs. This check only validates URL shape.",
            "notes": "WebSocket URL shape validated. Full Playwright/Puppeteer connection test requires browser client dependencies.",
        }
        return finish(PROVIDER, summary, raw)

    if not token:
        return missing_credentials(
            PROVIDER,
            ["BRIGHTDATA_SELENIUM_URL or BRIGHTDATA_BROWSER_WS_URL or BRIGHTDATA_API_KEY"],
            [
                "For Browser API Selenium: add BRIGHTDATA_SELENIUM_URL='https://USER:PASS@HOST:9515' to ~/.secrets",
                "For Browser API Playwright/Puppeteer: add BRIGHTDATA_BROWSER_WS_URL='wss://USER:PASS@HOST:9222' to ~/.secrets",
                "For REST account validation: add BRIGHTDATA_API_KEY='your_token' to ~/.secrets",
                "Rotate any credential pasted into chat before storing it.",
                "Set it with: export BRIGHTDATA_API_KEY='your_token'",
            ],
        )

    response = http_get("https://api.brightdata.com/customer/balance", headers={"Authorization": f"Bearer {token}"})
    raw["api_balance"] = response
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        **summaries,
        "docs": "https://docs.brightdata.com/",
        "cost_note": "Bright Data can be powerful but expensive. Validate specific dataset/Web Scraper API endpoints before enabling broad collection.",
    }
    return finish(PROVIDER, summary, redact_sensitive(raw))


if __name__ == "__main__":
    raise SystemExit(main())
