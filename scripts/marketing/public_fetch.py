"""Bounded public GETs with validated IPs pinned at connection, including redirects."""
from __future__ import annotations

import http.client
import io
import ipaddress
import socket
import ssl
import time
from urllib.parse import parse_qsl, urljoin, urlsplit

MAX_BYTES = 2_000_000
MAX_REDIRECTS = 5
TIMEOUT = 10


def validate_public_url(url: str):
    if any(ord(c) < 33 or ord(c) == 127 for c in url):
        raise ValueError('invalid URL characters')
    p = urlsplit(url)
    if p.scheme not in {'http', 'https'} or not p.hostname or p.username or p.password or p.fragment:
        raise ValueError('credential-free HTTP(S) URL without fragment required')
    if any(k.lower() in {'token', 'key', 'api_key', 'access_token', 'auth', 'code', 'email', 'password'} for k, _ in parse_qsl(p.query)):
        raise ValueError('sensitive query parameters are not retained')
    return p


def destination(url: str, *, fixture: bool = False):
    p = validate_public_url(url)
    host = p.hostname.encode('idna').decode('ascii')
    port = p.port or (443 if p.scheme == 'https' else 80)
    if not fixture and port not in {80, 443}:
        raise ValueError('public fetch allows only standard HTTP(S) ports')
    rows = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not rows:
        raise ValueError('no destination addresses')
    for family, _, _, _, address in rows:
        ip = ipaddress.ip_address(address[0])
        effective = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip
        if not effective.is_global and not (fixture and effective.is_loopback):
            raise ValueError('non-public destination blocked')
    return p, host, port, rows


class DeadlineReader(io.RawIOBase):
    def __init__(self, sock, deadline):
        super().__init__()
        self.sock, self.deadline = sock, deadline

    def readable(self):
        return True

    def readinto(self, buffer):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('fetch deadline exceeded')
        self.sock.settimeout(remaining)
        return self.sock.recv_into(buffer)


class DeadlineSocket:
    """Apply the total deadline to every header/body receive, including trickles."""
    def __init__(self, sock, deadline):
        self.sock, self.deadline = sock, deadline

    def makefile(self, mode):
        if mode != 'rb':
            raise ValueError('read-only response stream required')
        return io.BufferedReader(DeadlineReader(self.sock, self.deadline))

    def sendall(self, data):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('fetch deadline exceeded')
        self.sock.settimeout(remaining)
        self.sock.sendall(data)

    def close(self):
        # HTTPConnection detaches a close-delimited response before its body is
        # consumed. The fetch owner closes the transport after response.close().
        pass


def fetch(url: str, *, fixture: bool = False) -> dict:
    """No cookies, credentials, JS, ambient proxy, decompression or automatic retries."""
    source = url
    deadline = time.monotonic() + TIMEOUT
    redirects = []
    for hop in range(MAX_REDIRECTS + 1):
        p, host, port, rows = destination(url, fixture=fixture)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('fetch deadline exceeded')
        conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
        sock = None
        response = None
        try:
            # Connect to a validated numeric address, never resolve the host again.
            family, socktype, proto, _, address = rows[0]
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(remaining)
            sock.connect(address)
            if p.scheme == 'https':
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('fetch deadline exceeded')
                sock.settimeout(remaining)
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
            conn.sock = DeadlineSocket(sock, deadline)
            path = p.path or '/'
            if p.query:
                path += '?' + p.query
            host_header = f'[{host}]' if ':' in host else host
            if port != (443 if p.scheme == 'https' else 80):
                host_header += f':{port}'
            conn.request('GET', path, headers={'Host': host_header, 'User-Agent': 'EvidenceScout-LinkCheck/1',
                                             'Accept-Encoding': 'identity'})
            response = conn.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader('Location')
                if not location or hop == MAX_REDIRECTS:
                    raise ValueError('missing redirect destination or redirect limit reached')
                next_url = urljoin(url, location)
                if next_url == source or next_url in redirects:
                    raise ValueError('redirect loop')
                redirects.append(next_url)
                url = next_url
                continue
            if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
                raise ValueError('compressed response unsupported')
            chunks, size = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('fetch deadline exceeded')
                sock.settimeout(remaining)
                chunk = response.read1(min(65536, MAX_BYTES + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk); size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('response size limit exceeded')
            raw = b''.join(chunks)
            return {'source_url': source, 'final_url': url, 'redirects': redirects,
                    'status': response.status, 'content_type': response.getheader('Content-Type', ''), 'raw': raw}
        finally:
            if response is not None:
                response.close()
            conn.close()
            if sock is not None:
                sock.close()
    raise ValueError('redirect limit reached')
