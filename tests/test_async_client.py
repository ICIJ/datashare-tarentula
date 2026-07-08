from os.path import exists, join
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import aiohttp
import pytest
from aioresponses import CallbackResult, aioresponses

from tarentula.async_client import AsyncDatashareClient
from tarentula.async_csrf import async_fetch_datashare_csrf
from tarentula.datashare_client import (
    DATASHARE_CSRF_COOKIE_NAME,
    DATASHARE_CSRF_HEADER_NAME,
    HTTP_REQUEST_TIMEOUT_SEC,
)

DATASHARE_URL = 'http://datashare.test'
CSRF_TOKEN = 'csrf-token-value'


async def test_async_fetch_datashare_csrf_returns_token():
    with aioresponses() as mocked:
        mocked.get(
            f'{DATASHARE_URL}/api/users/me',
            status=200,
            body='{}',
            headers={'Set-Cookie': f'{DATASHARE_CSRF_COOKIE_NAME}={CSRF_TOKEN}; Path=/'},
        )
        async with aiohttp.ClientSession() as session:
            cookies, headers = await async_fetch_datashare_csrf(session, DATASHARE_URL)
    assert cookies == {DATASHARE_CSRF_COOKIE_NAME: CSRF_TOKEN}
    assert headers == {DATASHARE_CSRF_HEADER_NAME: CSRF_TOKEN}


async def test_async_fetch_datashare_csrf_no_token_returns_empty():
    with aioresponses() as mocked:
        mocked.get(f'{DATASHARE_URL}/api/users/me', status=200, body='{}')
        async with aiohttp.ClientSession() as session:
            cookies, headers = await async_fetch_datashare_csrf(session, DATASHARE_URL)
    assert cookies == {}
    assert headers == {}


async def test_async_fetch_datashare_csrf_swallows_errors():
    with aioresponses() as mocked:
        mocked.get(f'{DATASHARE_URL}/api/users/me',
                   exception=aiohttp.ClientConnectionError('boom'))
        async with aiohttp.ClientSession() as session:
            cookies, headers = await async_fetch_datashare_csrf(session, DATASHARE_URL)
    assert cookies == {}
    assert headers == {}


async def test_async_fetch_datashare_csrf_swallows_timeouts():
    import asyncio

    with aioresponses() as mocked:
        mocked.get(f'{DATASHARE_URL}/api/users/me',
                   exception=asyncio.TimeoutError())
        async with aiohttp.ClientSession() as session:
            cookies, headers = await async_fetch_datashare_csrf(session, DATASHARE_URL)
    assert cookies == {}
    assert headers == {}


from types import SimpleNamespace
from tarentula.async_client import AsyncDatashareClient


def make_sync_stub(datashare_url=DATASHARE_URL, elasticsearch_host=None):
    return SimpleNamespace(
        datashare_url=datashare_url,
        elasticsearch_host=elasticsearch_host or f'{datashare_url}/api/index/search',
        cookies={},
        headers=None,
    )


async def test_request_retries_once_after_403_with_new_csrf():
    url = f'{DATASHARE_URL}/api/index/search/idx/_search'
    with aioresponses() as mocked:
        mocked.post(url, status=403, body='{}')
        mocked.get(
            f'{DATASHARE_URL}/api/users/me',
            status=200,
            body='{}',
            headers={'Set-Cookie': f'{DATASHARE_CSRF_COOKIE_NAME}={CSRF_TOKEN}; Path=/'},
        )
        mocked.post(url, status=200, payload={'ok': True})
        async with AsyncDatashareClient(make_sync_stub()) as client:
            status, payload = await client.request('post', url, json={})
    assert status == 200
    assert payload == {'ok': True}


async def test_request_retries_transient_500_then_succeeds():
    url = f'{DATASHARE_URL}/api/index/search/idx/_search'
    with aioresponses() as mocked:
        mocked.post(url, status=503, body='{}')
        mocked.post(url, status=200, payload={'ok': True})
        async with AsyncDatashareClient(make_sync_stub(), max_retries=3) as client:
            status, payload = await client.request('post', url, json={})
    assert status == 200
    assert payload == {'ok': True}


async def test_request_persistent_403_after_refresh_returns_403():
    url = f'{DATASHARE_URL}/api/index/search/idx/_search'
    with aioresponses() as mocked:
        mocked.post(url, status=403, body='{}')
        mocked.get(
            f'{DATASHARE_URL}/api/users/me',
            status=200,
            body='{}',
            headers={'Set-Cookie': f'{DATASHARE_CSRF_COOKIE_NAME}={CSRF_TOKEN}; Path=/'},
        )
        mocked.post(url, status=403, body='{}')
        async with AsyncDatashareClient(make_sync_stub()) as client:
            status, payload = await client.request('post', url, json={})
    assert status == 403


async def test_request_transient_status_exhausts_retries():
    url = f'{DATASHARE_URL}/api/index/search/idx/_search'
    with aioresponses() as mocked:
        mocked.post(url, status=503, body='{}')
        mocked.post(url, status=503, body='{}')
        async with AsyncDatashareClient(make_sync_stub(), max_retries=1) as client:
            status, payload = await client.request('post', url, json={})
    assert status == 503


async def test_request_exception_exhausts_retries_and_raises():
    url = f'{DATASHARE_URL}/api/index/search/idx/_search'
    with aioresponses() as mocked:
        mocked.post(url, exception=aiohttp.ClientConnectionError('boom'))
        mocked.post(url, exception=aiohttp.ClientConnectionError('boom'))
        async with AsyncDatashareClient(make_sync_stub(), max_retries=1) as client:
            with pytest.raises(aiohttp.ClientError):
                await client.request('post', url, json={})


def _hit(n):
    return {'_id': f'id{n:02d}', '_source': {'name': f'n{n}'}, 'sort': ['n%d' % n, f'id{n:02d}']}


async def test_search_after_scan_paginates_without_dupes():
    host = f'{DATASHARE_URL}/api/index/search'
    url = f'{host}/idx/_search'
    captured = []

    def make_cb(page):
        def cb(url, **kwargs):
            captured.append(kwargs.get('json'))
            return CallbackResult(status=200, payload=page)
        return cb

    with aioresponses() as mocked:
        mocked.post(url, callback=make_cb({'hits': {'hits': [_hit(1), _hit(2)]}}))
        mocked.post(url, callback=make_cb({'hits': {'hits': [_hit(3), _hit(4)]}}))
        mocked.post(url, callback=make_cb({'hits': {'hits': []}}))
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            ids = [h['_id'] async for h in client.search_after_scan(index='idx', query={}, size=2)]

    assert ids == ['id01', 'id02', 'id03', 'id04']
    # First page must NOT send search_after; later pages must carry the previous page's last hit sort.
    assert 'search_after' not in captured[0]
    assert captured[1]['search_after'] == ['n2', 'id02']
    assert captured[2]['search_after'] == ['n4', 'id04']
    # Tiebreaker present on every page.
    for body in captured:
        assert body['sort'] == [{'_score': 'desc'}, {'_id': 'asc'}]


async def test_search_after_scan_first_page_only_honors_from():
    host = f'{DATASHARE_URL}/api/index/search'
    url = f'{host}/idx/_search'
    captured = []

    def make_cb(page):
        def cb(url, **kwargs):
            captured.append(kwargs.get('json'))
            return CallbackResult(status=200, payload=page)
        return cb

    with aioresponses() as mocked:
        mocked.post(url, callback=make_cb({'hits': {'hits': [_hit(1), _hit(2)]}}))
        mocked.post(url, callback=make_cb({'hits': {'hits': [_hit(3)]}}))
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            ids = [h['_id'] async for h in
                   client.search_after_scan(index='idx', query={}, size=2, from_=5)]

    assert ids == ['id01', 'id02', 'id03']
    # First page carries `from`; once search_after is set, `from` must never be sent again.
    assert captured[0]['from'] == 5
    assert 'search_after' not in captured[0]
    assert 'from' not in captured[1]
    assert captured[1]['search_after'] == ['n2', 'id02']


async def test_search_after_scan_honors_limit_mid_page():
    host = f'{DATASHARE_URL}/api/index/search'
    url = f'{host}/idx/_search'
    with aioresponses() as mocked:
        mocked.post(url, status=200, payload={'hits': {'hits': [_hit(1), _hit(2), _hit(3)]}})
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            ids = [h['_id'] async for h in client.search_after_scan(index='idx', query={}, size=3, limit=2)]
    assert ids == ['id01', 'id02']


async def test_open_pit_returns_none_when_unavailable():
    # A proxy/unmapped route can return a non-JSON error body (e.g. an HTML 404/405 page).
    # open_pit() must tolerate this and fall back to returning None instead of letting the
    # JSONDecodeError escape.
    host = f'{DATASHARE_URL}/api/index/search'
    with aioresponses() as mocked:
        mocked.post(f'{host}/idx/_pit?keep_alive=1m', status=405,
                    body='<html>Not Found</html>', content_type='text/html')
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            pit = await client.open_pit('idx')
    assert pit is None


async def test_scan_falls_back_to_search_after_without_pit():
    host = f'{DATASHARE_URL}/api/index/search'
    with aioresponses() as mocked:
        mocked.post(f'{host}/idx/_pit?keep_alive=1m', status=405, body='{}')
        mocked.post(f'{host}/idx/_search', status=200, payload={'hits': {'hits': [_hit(1)]}})
        mocked.post(f'{host}/idx/_search', status=200, payload={'hits': {'hits': []}})
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            ids = [h['_id'] async for h in client.search_after_scan(
                index='idx', query={}, size=2, use_pit=True)]
    assert ids == ['id01']


async def test_scan_falls_back_to_search_after_when_pit_returns_non_json():
    # Same fallback, but the /_pit error body is non-JSON (e.g. an HTML error page from a
    # proxy in front of an unmapped route), which used to raise JSONDecodeError and crash the
    # whole scan instead of gracefully falling back to plain search_after pagination.
    host = f'{DATASHARE_URL}/api/index/search'
    with aioresponses() as mocked:
        mocked.post(f'{host}/idx/_pit?keep_alive=1m', status=405,
                    body='<html>Not Found</html>', content_type='text/html')
        mocked.post(f'{host}/idx/_search', status=200, payload={'hits': {'hits': [_hit(1)]}})
        mocked.post(f'{host}/idx/_search', status=200, payload={'hits': {'hits': []}})
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            ids = [h['_id'] async for h in client.search_after_scan(
                index='idx', query={}, size=2, use_pit=True)]
    assert ids == ['id01']


async def test_scan_uses_pit_when_available():
    host = f'{DATASHARE_URL}/api/index/search'
    captured = []

    def make_cb(page):
        def cb(url, **kwargs):
            captured.append(kwargs.get('json'))
            return CallbackResult(status=200, payload=page)
        return cb

    deleted = {}

    def delete_cb(url, **kwargs):
        deleted['id'] = (kwargs.get('json') or {}).get('id')
        return CallbackResult(status=200, payload={'succeeded': True, 'num_freed': 1})

    with aioresponses() as mocked:
        mocked.post(f'{host}/idx/_pit?keep_alive=1m', status=200, payload={'id': 'PIT1'})
        mocked.post(f'{host}/_search', callback=make_cb(
            {'hits': {'hits': [_hit(1)]}, 'pit_id': 'PIT2'}))
        mocked.post(f'{host}/_search', callback=make_cb({'hits': {'hits': []}, 'pit_id': 'PIT2'}))
        mocked.delete(f'{host}/_pit', callback=delete_cb)
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            ids = [h['_id'] async for h in client.search_after_scan(
                index='idx', query={}, size=1, use_pit=True)]

    assert ids == ['id01']
    assert captured[0]['pit']['id'] == 'PIT1'
    assert captured[0]['sort'] == [{'_score': 'desc'}, {'_shard_doc': 'asc'}]
    assert captured[1]['pit']['id'] == 'PIT2'
    delete_calls = [key for key in mocked.requests if key[0].upper() == 'DELETE']
    assert delete_calls, 'expected the PIT to be closed via DELETE /_pit'
    # The PIT that is actually left open is the refreshed one, so that is what must be released.
    assert deleted['id'] == 'PIT2'


async def test_stream_download_writes_body_to_file():
    index = 'idx'
    doc_id = 'abc'
    url = f'{DATASHARE_URL}/api/{index}/documents/src/{doc_id}'
    with TemporaryDirectory() as tmp:
        dest = join(tmp, 'out.bin')
        with aioresponses() as mocked:
            mocked.get(f'{url}?routing={doc_id}', status=200, body=b'hello-bytes')
            async with AsyncDatashareClient(make_sync_stub()) as client:
                await client.stream_download(index, doc_id, doc_id, dest)
        with open(dest, 'rb') as handle:
            assert handle.read() == b'hello-bytes'


async def test_stream_download_retries_once_after_403_with_new_csrf():
    # stream_download must go through the same CSRF-refresh-once machinery as request():
    # a single 403 triggers a CSRF handshake and the download is retried and succeeds.
    index = 'idx'
    doc_id = 'abc'
    url = f'{DATASHARE_URL}/api/{index}/documents/src/{doc_id}?routing={doc_id}'
    with TemporaryDirectory() as tmp:
        dest = join(tmp, 'out.bin')
        with aioresponses() as mocked:
            mocked.get(url, status=403, body='{}')
            mocked.get(
                f'{DATASHARE_URL}/api/users/me',
                status=200,
                body='{}',
                headers={'Set-Cookie': f'{DATASHARE_CSRF_COOKIE_NAME}={CSRF_TOKEN}; Path=/'},
            )
            mocked.get(url, status=200, body=b'hello-bytes')
            async with AsyncDatashareClient(make_sync_stub()) as client:
                await client.stream_download(index, doc_id, doc_id, dest)
        with open(dest, 'rb') as handle:
            assert handle.read() == b'hello-bytes'


async def test_stream_download_bounds_inactivity_between_chunks():
    # A server that stalls mid-body (stops sending chunks without closing the connection) must
    # not hang the download forever: `total=None` keeps large-but-healthy transfers uncapped,
    # but `sock_read` bounds the inactivity gap between chunks so a stalled stream still times
    # out and lets the retry/backoff machinery (or a clean failure) take over.
    index = 'idx'
    doc_id = 'abc'
    url = f'{DATASHARE_URL}/api/{index}/documents/src/{doc_id}'
    captured = {}

    def cb(url, **kwargs):
        captured.update(kwargs)
        return CallbackResult(status=200, body=b'hello-bytes')

    with TemporaryDirectory() as tmp:
        dest = join(tmp, 'out.bin')
        with aioresponses() as mocked:
            mocked.get(f'{url}?routing={doc_id}', callback=cb)
            async with AsyncDatashareClient(make_sync_stub()) as client:
                await client.stream_download(index, doc_id, doc_id, dest)

    timeout = captured['timeout']
    assert timeout.total is None
    assert timeout.sock_read == HTTP_REQUEST_TIMEOUT_SEC


async def test_stream_download_non_2xx_raises_and_leaves_no_partial_file():
    # A terminal non-2xx status (not retried, since 404 is not a transient status) must raise
    # aiohttp.ClientResponseError and must not leave a partial file on disk.
    index = 'idx'
    doc_id = 'abc'
    url = f'{DATASHARE_URL}/api/{index}/documents/src/{doc_id}?routing={doc_id}'
    with TemporaryDirectory() as tmp:
        dest = join(tmp, 'out.bin')
        with aioresponses() as mocked:
            mocked.get(url, status=404, body='{}')
            async with AsyncDatashareClient(make_sync_stub()) as client:
                with pytest.raises(aiohttp.ClientResponseError):
                    await client.stream_download(index, doc_id, doc_id, dest)
        assert not exists(dest)
