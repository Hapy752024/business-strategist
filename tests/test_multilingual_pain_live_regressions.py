"""Regressions from the September multilingual retrieval pilot.

Synthetic/minimal phrases preserve failure identity without customer histories.
These verify lead retention, not firsthand voice or market validity.
"""
import argparse
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/evidence_scout"))
import collect as c


def assess(text, query, language="en"):
    args = argparse.Namespace(topic="personal insurance advice Germany PKV BU",
                              problem_keywords="", workaround_keywords="", language=language)
    return c.assess_relevance(text, args, query)


@pytest.mark.parametrize("text,query", [
    ("Disability insurance (BU) questions. Should I pay for advice without commissions?", "disability insurance Germany health questions reddit"),
    ("Insurance migration from public to private. Currently insured with TK.", "insurance broker Germany stopped responding reddit"),
    ("Is private insurance in Germany better? I want English support.", "private public health insurance Germany regret reddit"),
    ("BU: Gesundheitsfragen und meine Entscheidung", "BU Gesundheitsfragen Forum"),
])
def test_product_and_transition_language_remains_a_reviewable_lead(text, query):
    assert assess(text, query)[0] != "irrelevant"


@pytest.mark.parametrize("language,text,query", [
    ("fr", "Mon assurance refuse de rembourser et je cherche une solution.", "assurance refuse rembourser"),
    ("ar", "التأمين رفض المطالبة وأبحث عن حل", "التأمين رفض المطالبة"),
    ("ja", "保険の請求が拒否されました。相談したいです。", "保険の請求が拒否されました"),
])
def test_uncovered_language_is_not_rejected_by_german_english_lexicon(language, text, query):
    status, reason, _ = assess(text, query, language)
    assert status == "weak"
    assert "does not cover this language" in reason


@pytest.mark.parametrize("language,text,query", [
    ("de", "Immobilienmakler meldet sich wegen Hauskauf nicht.", "Makler meldet sich nicht Forum Versicherte"),
    ("en", "Public to private migration of cloud servers is painful.", "insurance advice Germany"),
    ("fr", "Recette de gâteau au chocolat", "assurance refuse rembourser"),
])
def test_missing_material_insurance_context_still_excludes_noise(language, text, query):
    assert assess(text, query, language)[0] == "irrelevant"


def test_ambiguous_broker_word_remains_unresolved_until_hydrated():
    status, reason, _ = assess("Mein Makler antwortet seit Wochen nicht.", "Makler meldet sich nicht Forum", "de")
    assert status == "weak"
    assert "Ambiguous broker" in reason


def test_real_estate_episode_does_not_become_insurance_pain_from_makler():
    assert assess("Makler meldet sich nicht: Vor zwei Wochen eine Immobilie besichtigt.",
                  "Makler meldet sich nicht Forum Versicherte", "de")[0] == "irrelevant"
