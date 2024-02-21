import httpx


class BaseSite:

    def __init__(self, url):
        self.url = url
        self.name = self.__class__.__name__

    async def get(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.url}: {response.text}")

        return response.text

    async def crawl(self):
        pass

    def get_link(self, path):
        if path.startswith("/") and self.url.endswith("/"):
            path = path[1:]

        return f"{self.url}{path}"