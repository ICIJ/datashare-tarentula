from types import SimpleNamespace

import aiohttp
import pytest
from aioresponses import aioresponses

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
