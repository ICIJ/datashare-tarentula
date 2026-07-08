from types import SimpleNamespace

import aiohttp
import pytest
from aioresponses import CallbackResult, aioresponses

from tarentula.async_client import AsyncDatashareClient
from tarentula.async_csrf import async_fetch_datashare_csrf
from tarentula.datashare_client import (
    DATASHARE_CSRF_COOKIE_NAME,
    DATASHARE_CSRF_HEADER_NAME,
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


async def test_search_after_scan_honors_limit_mid_page():
    host = f'{DATASHARE_URL}/api/index/search'
    url = f'{host}/idx/_search'
    with aioresponses() as mocked:
        mocked.post(url, status=200, payload={'hits': {'hits': [_hit(1), _hit(2), _hit(3)]}})
        async with AsyncDatashareClient(make_sync_stub(elasticsearch_host=host)) as client:
            ids = [h['_id'] async for h in client.search_after_scan(index='idx', query={}, size=3, limit=2)]
    assert ids == ['id01', 'id02']
