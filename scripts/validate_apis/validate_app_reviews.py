#!/usr/bin/env python3
from __future__ import annotations

from common import finish, get_secret, missing_credentials


PROVIDER = "app_reviews"


def main() -> int:
    google_name, google_creds = get_secret("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "GOOGLE_APPLICATION_CREDENTIALS")
    apple_key_name, apple_key = get_secret("APPSTORE_CONNECT_KEY_ID")
    apple_issuer_name, apple_issuer = get_secret("APPSTORE_CONNECT_ISSUER_ID")
    if not google_creds and not (apple_key and apple_issuer):
        return missing_credentials(
            PROVIDER,
            [
                "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS",
                "APPSTORE_CONNECT_KEY_ID and APPSTORE_CONNECT_ISSUER_ID",
            ],
            [
                "Google Play owned-app reviews: set up API access at https://developers.google.com/android-publisher/getting_started",
                "Apple owned-app reviews: set up App Store Connect API access at https://developer.apple.com/documentation/appstoreconnectapi",
                "For competitor reviews, validate APIFY_TOKEN, SERPAPI_API_KEY, or BRIGHTDATA_API_KEY instead.",
                "This script currently checks credential presence only; provider-specific owned-app calls need app/package IDs.",
            ],
        )

    summary = {
        "status": "ok",
        "credential_source": {
            "google": google_name if google_creds else None,
            "apple_key": apple_key_name if apple_key else None,
            "apple_issuer": apple_issuer_name if apple_issuer else None,
        },
        "docs": [
            "https://developers.google.com/android-publisher/reply-to-reviews",
            "https://developer.apple.com/documentation/appstoreconnectapi",
        ],
        "cost_note": "Official app review APIs are primarily for owned apps. Competitor review mining needs a third-party provider or public-source workflow.",
        "next_step": "Add --package-name or --apple-app-id support once target owned apps are known.",
    }
    return finish(PROVIDER, summary, {"note": "Credential presence validation only."})


if __name__ == "__main__":
    raise SystemExit(main())
