import asyncio
import os
from json import JSONDecodeError

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
        return await self._send(method, url, params=params, json=json)

    async def stream_download(self, index, doc_id, routing, dest_path):
        url = urljoin(self.sync.datashare_url, 'api', index, '/documents/src', doc_id)
        await self._send('get', url, params={'routing': routing}, stream_to=dest_path)

    @staticmethod
    async def _parse_json(response):
        try:
            return await response.json(content_type=None)
        except (JSONDecodeError, ValueError, aiohttp.ContentTypeError):
            # A proxy (or an unmapped route) can hand back a non-JSON error body (e.g. an
            # HTML 404/405 page). Treat it as an empty payload rather than letting the parse
            # error escape and crash the caller (this is what lets open_pit() gracefully
            # fall back to plain search_after pagination).
            return {}

    @staticmethod
    async def _stream_to_file(response, dest_path):
        try:
            with open(dest_path, 'wb') as handle:
                async for chunk in response.content.iter_chunked(1 << 16):
                    handle.write(chunk)
        except BaseException:
            try:
                os.remove(dest_path)
            except OSError:
                pass
            raise

    async def _send(self, method, url, *, params=None, json=None, stream_to=None):
        """One-attempt-with-retries request. Applies the CSRF-403-refresh-once and transient
        (429/502/503/504 + connection/timeout) backoff-retry logic shared by both plain JSON
        requests and file downloads. Once a terminal (non-retried) response is reached, either
        parses it as JSON (`stream_to is None`) or streams its body to `stream_to`, returning
        `(status, payload)` or `(status, None)` respectively."""
        if stream_to is not None:
            # total=None so legitimately large files are never capped by an overall deadline;
            # sock_read bounds inactivity between chunks so a server that stalls mid-body (stops
            # sending data without closing the connection) cannot hang iter_chunked() forever.
            timeout = aiohttp.ClientTimeout(total=None, sock_connect=HTTP_REQUEST_TIMEOUT_SEC,
                                            sock_read=HTTP_REQUEST_TIMEOUT_SEC)
        else:
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
                    if stream_to is not None:
                        response.raise_for_status()
                        await self._stream_to_file(response, stream_to)
                        return response.status, None
                    payload = await self._parse_json(response)
                    return response.status, payload
            except aiohttp.ClientResponseError:
                # Raised by raise_for_status() above for a terminal non-2xx status: this is not
                # a transient/connection failure, so it must not be retried.
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt >= self.max_retries:
                    raise
                logger.debug('Transient async request error (%s), retrying', exc)
                await asyncio.sleep(BACKOFF_BASE_SEC * (2 ** attempt))
                attempt += 1

    async def open_pit(self, index, keep_alive='1m'):
        url = urljoin(self.sync.elasticsearch_host, index, '/_pit')
        status, payload = await self.request('post', url, params={'keep_alive': keep_alive})
        if status < 400 and payload.get('id'):
            return payload['id']
        return None

    async def close_pit(self, pit_id):
        url = urljoin(self.sync.elasticsearch_host, '/_pit')
        try:
            await self.request('delete', url, json={'id': pit_id})
        # Best-effort close: on Ctrl-C the session may already be closed by the time this runs,
        # in which case self.request() raises RuntimeError('Session is closed') rather than an
        # aiohttp.ClientError/asyncio.TimeoutError. Swallow that too instead of letting it mask
        # the original cancellation.
        except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError):
            pass

    async def _paginate_search_after(self, *, url, body, size, limit, from_, on_payload=None):
        """Shared search_after page loop, used by both the index-based and the
        PIT-based scan. `body` already carries the tiebreaker sort (and, for the
        PIT path, the caller keeps its `pit` entry current via `on_payload`)."""
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
            if on_payload is not None:
                on_payload(payload)
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

    async def search_after_scan(self, *, index, query, source=None,
                                sort_by='_score', order_by='desc', size=1000, limit=0,
                                from_=0, use_pit=False, keep_alive='1m'):
        pit_id = await self.open_pit(index, keep_alive) if use_pit else None
        if pit_id is None:
            url = urljoin(self.sync.elasticsearch_host, index, '/_search')
            sort = [{sort_by: order_by}]
            if sort_by != '_id':
                sort.append({'_id': 'asc'})
            body = {**(query or {}), 'sort': sort, 'size': size}
            if source is not None:
                body['_source'] = source
            async for hit in self._paginate_search_after(
                    url=url, body=body, size=size, limit=limit, from_=from_):
                yield hit
            return

        # ES may hand back a refreshed pit_id mid-scan; track it so the finally
        # closes the context that is actually still open, not the stale original.
        current_pit_id = pit_id
        try:
            url = urljoin(self.sync.elasticsearch_host, '/_search')
            sort = [{sort_by: order_by}]
            if sort_by != '_shard_doc':
                sort.append({'_shard_doc': 'asc'})
            body = {**(query or {}), 'sort': sort, 'size': size}
            if source is not None:
                body['_source'] = source

            def refresh_pit(payload):
                nonlocal current_pit_id
                if payload.get('pit_id'):
                    current_pit_id = payload['pit_id']
                body['pit'] = {'id': current_pit_id, 'keep_alive': keep_alive}

            refresh_pit({})
            async for hit in self._paginate_search_after(
                    url=url, body=body, size=size, limit=limit, from_=from_,
                    on_payload=refresh_pit):
                yield hit
        finally:
            await self.close_pit(current_pit_id)
