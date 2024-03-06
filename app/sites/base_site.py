import asyncio
import logging
import traceback

logger = logging.getLogger(__name__)


class BaseSite:

    def __init__(self, url, path, start_page=1, end_page=1, page_crawl_delay=0.5):
        self.url = url
        self.path = path
        self.start_page = start_page
        self.end_page = end_page
        self.page_crawl_delay = page_crawl_delay
        self.name = self.__class__.__name__

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
