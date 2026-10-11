"""Capture-backed link observations. These describe a dated page, not SEO uplift."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit, urlunsplit

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / 'schemas/link-observation.schema.json').read_text())


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def url_key(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
        raise ValueError('credential-free HTTP(S) URL required')
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or '/', parts.query, ''))


def resolve_bytes(base: Path | None, relative: str, staged: dict | None = None) -> bytes:
    """Same path checks apply to staged and persisted evidence; no symlink hops."""
    rel = PurePosixPath(relative)
    if not relative or '\\' in relative or rel.is_absolute() or '..' in rel.parts or str(rel) != relative:
        raise ValueError('unsafe evidence path')
    if base is None:
        raise ValueError('evidence root unresolved')
    base = Path(base).absolute()
    current = base
    if any(p.is_symlink() for p in (current, *current.parents)):
        raise ValueError('symlink evidence root')
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('symlink evidence path')
    if not current.resolve().is_relative_to(base.resolve()):
        raise ValueError('evidence path escapes root')
    if staged and relative in staged:
        raw = staged[relative]
        return raw.encode('utf-8') if isinstance(raw, str) else raw
    return current.read_bytes()


def bound_bytes(binding: dict, base: Path | None, staged: dict | None = None) -> bytes:
    raw = resolve_bytes(base, binding['path'], staged)
    if sha(raw) != binding['sha256']:
        raise ValueError('evidence digest changed: ' + binding['path'])
    return raw


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.base = None
        self.rows = []
        self.active = None
        self.template_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'template':
            self.template_depth += 1
        if self.template_depth:
            return
        attrs = dict(attrs)
        if tag == 'base' and self.base is None and attrs.get('href'):
            self.base = attrs['href']
        if tag == 'a':
            self.handle_endtag('a')
            if attrs.get('href'):
                self.active = {'href': attrs['href'], 'text': '',
                               'rel': sorted(set((attrs.get('rel') or '').lower().split()))}

    def handle_data(self, data):
        if self.active is not None and not self.template_depth:
            self.active['text'] += data

    def handle_startendtag(self, tag, attrs):
        # HTML templates are non-void: a slash does not close their inert subtree.
        if tag == 'template':
            self.handle_starttag(tag, attrs)
        else:
            super().handle_startendtag(tag, attrs)

    def handle_endtag(self, tag):
        if self.template_depth:
            if tag == 'template':
                self.template_depth -= 1
            return
        if tag == 'a' and self.active is not None:
            self.active['text'] = ' '.join(self.active['text'].split())
            self.rows.append(self.active)
            self.active = None


def anchors(raw: bytes, final_url: str) -> list[dict]:
    parser = Anchors()
    parser.feed(raw.decode('utf-8', errors='replace'))
    parser.handle_endtag('a')
    base = urljoin(final_url, parser.base) if parser.base else final_url
    result = []
    for row in parser.rows:
        try:
            href = url_key(urljoin(base, row['href']))
        except ValueError:
            continue
        result.append({**row, 'href': href})
    return result


def observe(raw: bytes, *, source_url: str, final_url: str, target_url: str,
            capture_path: str, ident: str, status: int | None = 200,
            redirects: list[str] | None = None, method: str = 'http',
            reason: str | None = None, checked_at: str | None = None) -> dict:
    source_url, final_url, target_url = map(url_key, (source_url, final_url, target_url))
    rows = anchors(raw, final_url) if status == 200 else []
    outcome = ('present' if any(row['href'] == target_url for row in rows) else 'absent') if status == 200 else (
        'access_limited' if status in {401, 403, 429} else 'fetch_error')
    return {'schema_version': 1, 'id': ident, 'source_url': source_url, 'final_url': final_url,
            'target_url': target_url, 'checked_at': checked_at or datetime.now(timezone.utc).isoformat(),
            'outcome': outcome, 'http_status': status, 'anchors': rows,
            'redirects': redirects or [], 'capture': {'path': capture_path, 'sha256': sha(raw)},
            'capture_method': method, 'parser_version': 'html-anchors-v1', 'reason': reason}


def validate(document: dict, base: Path | None, staged: dict | None = None,
             expected_source: str | None = None, expected_target: str | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(document)]
    if errors:
        return errors
    try:
        for field in ('source_url', 'final_url', 'target_url'):
            url_key(document[field])
        chain = [url_key(u) for u in document['redirects']]
        if document['source_url'] != document['final_url'] and (not chain or chain[-1] != document['final_url']):
            errors.append('redirect chain does not reach final URL')
        if expected_source and url_key(expected_source) != url_key(document['source_url']):
            errors.append('observation source differs from action')
        if expected_target and url_key(expected_target) != url_key(document['target_url']):
            errors.append('observation target differs from action')
        if datetime.fromisoformat(document['checked_at'].replace('Z', '+00:00')).utcoffset() is None:
            errors.append('checked_at requires timezone')
        raw = bound_bytes(document['capture'], base, staged)
        rows = anchors(raw, document['final_url']) if document['http_status'] == 200 else []
        if rows != document['anchors']:
            errors.append('recorded anchors differ from retained capture')
        derived = observe(raw, source_url=document['source_url'], final_url=document['final_url'],
                          target_url=document['target_url'], capture_path=document['capture']['path'],
                          ident=document['id'], status=document['http_status'])['outcome']
        if derived != document['outcome']:
            errors.append('outcome differs from retained capture')
    except (ValueError, OSError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    return errors


def validate_binding(binding: dict, base: Path | None, staged: dict | None,
                     source: str, target: str) -> list[str]:
    try:
        document = json.loads(bound_bytes(binding, base, staged))
        errors = validate(document, base, staged, source, target)
        if document.get('outcome') != 'present':
            errors.append('placement is not observed present')
        return errors
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        return [str(exc)]
