import httpx


class BaseSite:

    def __init__(self, url):
        self.url = url
        self.name = self.__class__.__name__

    async def crawl(self):
        pass

    def get_link(self, path):
        if path.startswith("/") and self.url.endswith("/"):
            path = path[1:]

        return f"{self.url}{path}"