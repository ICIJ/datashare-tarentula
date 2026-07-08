import asyncio

import aiohttp

from tarentula.async_csrf import async_fetch_datashare_csrf
from tarentula.datashare_client import HTTP_REQUEST_TIMEOUT_SEC, urljoin
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

    async def stream_download(self, index, doc_id, routing, dest_path):
        url = urljoin(self.sync.datashare_url, 'api', index, '/documents/src', doc_id)
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=HTTP_REQUEST_TIMEOUT_SEC)
        async with self._session.get(
                url, params={'routing': routing},
                cookies=self._merged_cookies(), headers=self._merged_headers(),
                timeout=timeout) as response:
            response.raise_for_status()
            with open(dest_path, 'wb') as handle:
                async for chunk in response.content.iter_chunked(1 << 16):
                    handle.write(chunk)

    async def search_after_scan(self, *, index, query, source=None,
                                sort_by='_score', order_by='desc', size=1000, limit=0, from_=0):
        url = urljoin(self.sync.elasticsearch_host, index, '/_search')
        sort = [{sort_by: order_by}, {'_id': 'asc'}]
        body = {**(query or {}), 'sort': sort, 'size': size}
        if source is not None:
            body['_source'] = source
        search_after = None
        yielded = 0
        while True:
            page_body = dict(body)
            if search_after is not None:
                page_body['search_after'] = search_after
            elif from_:
                page_body['from'] = from_
            status, payload = await self.request('post', url, json=page_body)
            if status >= 400:
                raise RuntimeError(f'Search failed with status {status}: {payload}')
            hits = payload.get('hits', {}).get('hits', [])
            if not hits:
                return
            for hit in hits:
                yield hit
                yielded += 1
                if limit and yielded >= limit:
                    return
            if len(hits) < size:
                return
            search_after = hits[-1].get('sort')
            if search_after is None:
                return
