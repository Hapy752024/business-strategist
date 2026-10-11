from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import socket
from unittest.mock import patch

import pytest

from scripts.marketing.public_fetch import destination, fetch
from scripts.marketing.verify_links import inspect


@pytest.mark.parametrize('host',['127.0.0.1','169.254.169.254','10.0.0.1','::ffff:127.0.0.1'])
def test_private_destinations_never_connect(host):
    with patch('socket.getaddrinfo', return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',(host,80))]):
        with pytest.raises(ValueError,match='non-public'):
            destination('http://publisher.example/')


@pytest.mark.parametrize('url',['file:///tmp/a','http://a:b@example.com/','https://example.com/?token=secret','https://example.com:8443/'])
def test_disallowed_urls(url):
    with pytest.raises(ValueError): destination(url)


def test_actual_http_relative_anchor_redirect_and_access_status():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/redirect':
                self.send_response(302);self.send_header('Location','/page');self.end_headers();return
            if self.path=='/loop':
                self.send_response(302);self.send_header('Location','/loop');self.end_headers();return
            status=403 if self.path=='/blocked' else 200
            self.send_response(status);self.send_header('Content-Type','text/html');self.end_headers()
            self.wfile.write(b'<base href="https://asset.example/"><a href="guide" rel="nofollow sponsored">Guide</a>')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin=f'http://127.0.0.1:{server.server_port}'
    try:
        doc,raw=inspect(origin+'/redirect','https://asset.example/guide',ident='one',capture_path='page.html',fixture=True)
        assert doc['outcome']=='present' and doc['final_url']==origin+'/page'
        assert doc['anchors'][0]['rel']==['nofollow','sponsored']
        assert inspect(origin+'/blocked','https://asset.example/guide',ident='b',capture_path='b.html',fixture=True)[0]['outcome']=='access_limited'
        assert inspect(origin+'/loop','https://asset.example/guide',ident='c',capture_path='c.html',fixture=True)[0]['outcome']=='fetch_error'
    finally:
        server.shutdown();server.server_close();thread.join()


def test_rebinding_cannot_change_connection_address():
    addresses=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',80))]
    with patch('socket.getaddrinfo',return_value=addresses) as dns, patch('socket.socket') as sock:
        sock.return_value.connect.side_effect=OSError('fixture stop')
        with pytest.raises(OSError):fetch('http://publisher.example/')
        dns.assert_called_once()
        sock.return_value.connect.assert_called_once_with(('93.184.216.34',80))


def test_mixed_public_private_dns_is_rejected_before_connect():
    rows = [(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,80))
            for ip in ['93.184.216.34','10.0.0.1']]
    with patch('socket.getaddrinfo',return_value=rows), patch('socket.socket') as sock:
        with pytest.raises(ValueError,match='non-public'):
            fetch('http://publisher.example/')
        sock.assert_not_called()


def test_redirect_private_hop_and_response_limits():
    from scripts.marketing import public_fetch
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/private':
                self.send_response(302); self.send_header('Location','http://169.254.169.254/latest/'); self.end_headers(); return
            self.send_response(200); self.send_header('Content-Type','text/html')
            if self.path == '/compressed': self.send_header('Content-Encoding','gzip')
            self.end_headers()
            self.wfile.write(b'a' * 101)
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin=f'http://127.0.0.1:{server.server_port}'
    try:
        with pytest.raises(ValueError,match='non-public'): fetch(origin+'/private',fixture=True)
        with pytest.raises(ValueError,match='compressed'): fetch(origin+'/compressed',fixture=True)
        with patch.object(public_fetch,'MAX_BYTES',100):
            with pytest.raises(ValueError,match='size limit'): fetch(origin+'/large',fixture=True)
    finally:
        server.shutdown();server.server_close();thread.join()
