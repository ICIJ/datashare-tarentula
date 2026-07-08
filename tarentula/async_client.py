import asyncio

import aiohttp

from tarentula.async_csrf import async_fetch_datashare_csrf
from tarentula.datashare_client import HTTP_REQUEST_TIMEOUT_SEC
from tarentula.logger import logger

TRANSIENT_STATUSES = {429, 502, 503, 504}
BACKOFF_BASE_SEC = 0.5


class AsyncDatashareClient:
    def __init__(self, sync_client, concurrency=5, max_retries=3):
        self.sync = sync_client
        self.concurrency = concurrency
        self.max_retries = max_retries
        self._csrf_cookies = {}
        self._csrf_headers = {}
        self._session = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        self._session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, *exc):
        await self._session.close()

    def _merged_cookies(self):
        return {**(self.sync.cookies or {}), **self._csrf_cookies}

    def _merged_headers(self):
        return {**(self.sync.headers or {}), **self._csrf_headers} or None

    async def _refresh_csrf(self):
        cookies, headers = await async_fetch_datashare_csrf(
            self._session, self.sync.datashare_url,
            headers=self.sync.headers, cookies=self.sync.cookies)
        if cookies:
            self._csrf_cookies = cookies
            self._csrf_headers = headers
            return True
        return False

    async def request(self, method, url, *, params=None, json=None):
        timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SEC)
        attempt = 0
        refreshed = False
        while True:
            try:
                async with self._session.request(
                        method, url, params=params, json=json,
                        cookies=self._merged_cookies(), headers=self._merged_headers(),
                        timeout=timeout) as response:
                    if response.status == 403 and not refreshed:
                        refreshed = await self._refresh_csrf()
                        if refreshed:
                            continue
                    if response.status in TRANSIENT_STATUSES and attempt < self.max_retries:
                        await asyncio.sleep(BACKOFF_BASE_SEC * (2 ** attempt))
                        attempt += 1
                        continue
                    payload = await response.json(content_type=None)
                    return response.status, payload
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt >= self.max_retries:
                    raise
                logger.debug('Transient async request error (%s), retrying', exc)
                await asyncio.sleep(BACKOFF_BASE_SEC * (2 ** attempt))
                attempt += 1
