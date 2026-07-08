import aiohttp
from aioresponses import aioresponses

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
