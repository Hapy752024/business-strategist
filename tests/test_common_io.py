import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common_io import now_iso, read_json, slugify, write_json


def test_write_json_bytes_and_parent_creation(tmp_path):
    target = tmp_path / "a" / "b" / "data.json"
    write_json(target, {"b": 1, "a": "é"})
    assert target.read_bytes() == '{\n  "b": 1,\n  "a": "é"\n}\n'.encode("utf-8")


def test_read_json_round_trip(tmp_path):
    target = tmp_path / "data.json"
    write_json(target, {"k": [1, 2, "ü"]})
    assert read_json(target) == {"k": [1, 2, "ü"]}


def test_now_iso_is_utc_seconds_with_z():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", now_iso())


def test_slugify_lowercase_ascii_dash_separated():
    assert slugify("  Hello, World!  ") == "hello-world"
    assert slugify("Café Münster -- 2026") == "cafe-munster-2026"


def test_slugify_truncates_without_trailing_dash():
    assert slugify("abc def ghi", max_len=4) == "abc"
    assert len(slugify("x" * 100)) == 60
