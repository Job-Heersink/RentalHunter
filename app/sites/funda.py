import asyncio
import logging
import re
import time

import httpx
from bs4 import BeautifulSoup, element

from app.database.house import House
from app.sites.base_site import BaseSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Funda(BaseSite):

    def __init__(self):
        super().__init__('https://www.funda.nl', "/zoeken/huur/", end_page=35)

    async def get(self, page=1):
        logger.info(f'fetching page {self.get_link()}?search_result={page}&selected_area=["nl"]')
        async with httpx.AsyncClient() as client:
            response = await client.get(self.get_link(),
                                        params={"search_result": page, "selected_area": '["nl"]'},
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"})

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.get_link()}: {response.text}")

        return response.text

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.select("div[class='pt-4']")
        houses_page = houses_page[0]

        for house in houses_page.children:
            try:
                if type(house) == element.Tag:
                    paths = house.find_all("a", {"class": "h-full"})
                    if len(paths) == 0:
                        continue
                    assert len(paths) == 1

                    link = paths[0]['href']
                    address = house.find("h2", {"data-test-id": "street-name-house-number"}).text.replace("\n",
                                                                                                          "").lstrip().rstrip()
                    city_postalcode = house.find("div", {"data-test-id": "postal-code-city"}).text.replace("\n",
                                                                                                           "").lstrip().rstrip()
                    postal_nr, postal_abc, city = city_postalcode.split(" ", 2)
                    postal_code = f"{postal_nr} {postal_abc}"
                    available = True
                    price = re.sub(r"\D", "", house.find("p", {"data-test-id": "price-rent"}).text)
                    square_meters = re.sub(r"\D", "",
                                           house.select("ul[class='mt-1 flex h-6 min-w-0 flex-wrap overflow-hidden']")[
                                               0].contents[0].text)
                    if square_meters == "":
                        continue
                    logger.debug(city)
                    houses.append(
                        House(source=self.name, city=city, address=address, link=link, price=price,
                              available=available, square_meters=square_meters, postalcode=postal_code))
            except Exception as e:
                logger.error(f"Failed to parse house: {e}")
                logger.error(f"on Address: {address}")


if __name__ == '__main__':
    asyncio.run(Funda().crawl())
