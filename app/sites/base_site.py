import asyncio
import logging
import traceback

import httpx

logger = logging.getLogger(__name__)


class BaseSite:

    def __init__(self, url, path, start_page=1, end_page=1, page_crawl_delay=0.5):
        self.url = url
        self.path = path
        self.start_page = start_page
        self.end_page = end_page
        self.page_crawl_delay = page_crawl_delay
        self.name = self.__class__.__name__

    async def _request(self, client_method, **kwargs):
        max_retries = 5
        headers = kwargs.get("headers", {})
        kwargs.pop("headers", None)
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"

        for i in range(max_retries):
            try:
                response = await client_method(**kwargs, headers=headers)

                if response.status_code >= 400:
                    raise Exception(f"Failed to fetch {self.get_link()}: ({response.status_code}) {response.text}")

                return response
            except httpx.ConnectTimeout as e:
                logger.error(f"ConnectTimeout: {e}. Retrying... ({i + 1}/{max_retries})")
                await asyncio.sleep(5)
            except httpx.ReadTimeout as e:
                logger.error(f"ReadTimeout: {e}. Retrying... ({i + 1}/{max_retries})")
                await asyncio.sleep(5)

    async def post(self, **kwargs):
        async with httpx.AsyncClient(timeout=10) as client:
            return await self._request(client.post, **kwargs)

    async def get(self, **kwargs):
        async with httpx.AsyncClient(timeout=10) as client:
            return await self._request(client.get, **kwargs)

    async def crawl(self):
        houses = []
        try:
            tasks = []

            for p in range(self.start_page, self.end_page + 1):
                tasks.append(asyncio.create_task(self.crawl_page(p, houses)))
                await asyncio.sleep(self.page_crawl_delay)

            await asyncio.gather(*tasks)

        except Exception as e:
            traceback.print_exc()
            logger.error(f"Failed to crawl {self.name}: {e}")
        finally:
            return houses

    async def crawl_page(self, page, houses):
        raise NotImplementedError

    def get_link(self, path=None):
        if path is None:
            path = self.path

        if path.startswith("/") and self.url.endswith("/"):
            path = path[1:]

        return f"{self.url}{path}"
