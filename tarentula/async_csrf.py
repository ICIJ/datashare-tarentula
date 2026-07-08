import asyncio

import aiohttp

from tarentula.datashare_client import (
    DATASHARE_CSRF_COOKIE_NAME,
    DATASHARE_CSRF_HEADER_NAME,
    HTTP_REQUEST_TIMEOUT_SEC,
    urljoin,
)
from tarentula.logger import logger


async def async_fetch_datashare_csrf(session, datashare_url, headers=None, cookies=None):
    # Datashare sets the CSRF cookie on a successful GET to /api/* only for authenticated
    # requests, so forward any auth headers/cookies the caller already has.
    url = urljoin(datashare_url, '/api/users/me')
    timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SEC)
    try:
        async with session.get(url, headers=headers, cookies=cookies, timeout=timeout) as response:
            token = response.cookies.get(DATASHARE_CSRF_COOKIE_NAME)
            token = token.value if token is not None else None
            if token:
                return ({DATASHARE_CSRF_COOKIE_NAME: token},
                        {DATASHARE_CSRF_HEADER_NAME: token})
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        logger.debug('Async CSRF token fetch failed: %s', exc)
    return {}, {}
