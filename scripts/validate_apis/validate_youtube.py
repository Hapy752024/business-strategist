#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "youtube"


def main() -> int:
    key_name, api_key = get_secret("YOUTUBE_API_KEY", "GOOGLE_API_KEY")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["YOUTUBE_API_KEY"],
            [
                "Open https://console.cloud.google.com/apis/library/youtube.googleapis.com",
                "Create/select a Google Cloud project and enable YouTube Data API v3",
                "Create an API key at https://console.cloud.google.com/apis/credentials",
                "Set it with: export YOUTUBE_API_KEY='your_key'",
                "Or add YOUTUBE_API_KEY=your_key to ~/.secrets",
            ],
        )

    query = cli_arg("query", "project management pain points")
    search_url = with_query(
        "https://www.googleapis.com/youtube/v3/search",
        {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 3,
            "key": api_key,
        },
    )
    search_response = http_get(search_url)
    raw = {"search": search_response}
    status = status_from_response(search_response)
    comment_status = "not_run"
    comment_count = 0
    if status == "ok":
        items = (search_response.get("body") or {}).get("items", [])
        video_id = None
        if items:
            video_id = items[0].get("id", {}).get("videoId")
        if video_id:
            comments_url = with_query(
                "https://www.googleapis.com/youtube/v3/commentThreads",
                {
                    "part": "snippet",
                    "videoId": video_id,
                    "maxResults": 5,
                    "textFormat": "plainText",
                    "key": api_key,
                },
            )
            comments_response = http_get(comments_url)
            raw["comments"] = comments_response
            comment_status = status_from_response(comments_response)
            if comment_status == "ok":
                comment_count = len((comments_response.get("body") or {}).get("items", []))

    summary = {
        "status": status,
        "credential_source": key_name,
        "query": query,
        "http_status": search_response.get("status_code"),
        "fields": fields_present(search_response.get("body")),
        "video_count": len((search_response.get("body") or {}).get("items", [])) if status == "ok" else 0,
        "comment_fetch_status": comment_status,
        "comment_count": comment_count,
        "transcript_status": transcript_probe()[0],
        "transcript_note": "Transcripts use youtube_transcript_api (no API key/quota). Status ok means transcript collection via collect.py --youtube-transcripts will work.",
        "docs": "https://developers.google.com/youtube/v3/getting-started",
        "cost_note": "Default YouTube quota is quota-unit based. Search and comment reads consume quota; confirm current costs in Google docs.",
    }
    return finish(PROVIDER, summary, raw)


def transcript_probe() -> tuple[str, int]:
    """Probe youtube_transcript_api against a captioned video. Returns (status, segment_count)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return "missing_module", 0
    try:
        fetched = YouTubeTranscriptApi().fetch("8jPQjjsBbIc")  # TED talk with captions
        return "ok", len(list(fetched))
    except Exception as exc:  # noqa: BLE001 - several HTTP/IP-block error types
        return f"error:{type(exc).__name__}", 0


if __name__ == "__main__":
    raise SystemExit(main())
