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


class Rebo(BaseSite):

    def __init__(self):
        super().__init__('https://www.rebohuurwoning.nl', '/nl/aanbod/')

    async def get(self, page=1):
        return (await super().get(url=self.get_link())).text

    async def crawl_page(self, page, houses):
        html = await self.get()
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.select("div[class='row js-object-items']")
        assert len(houses_page) == 1
        houses_page = houses_page[0].contents[0]

        for house in houses_page.children:
            if type(house) == element.Tag:
                house = house.contents[0]
                lat = house.get('data-lat', None)
                lon = house.get('data-lng', None)
                path = house.find("a", recursive=False)['href']
                available = True
                city = house.find("div", {"class": "text"}, recursive=False).find("h4").text
                address = house.find("div", {"class": "text"}, recursive=False).find("p").text
                try:
                    price = re.sub(r"\D", "",house.find("div", {"class": "details"}).find("div", {"class": "price"}).text)
                    if price == "":
                        continue
                except Exception as e:
                    logger.warning(f"Failed to parse price: {e} for house: {address} in {city}")
                    continue

                try:
                    square_meters = re.sub(r"\D", "", house.find("div", {"class": "details"}).find("div", {
                        "class": "measurements"}).text.split("m")[0])
                except Exception as e:
                    logger.warning(f"Failed to parse square meters: {e} for house: {address} in {city}")
                    square_meters = None

                try:
                    bedrooms = re.sub(r"\D", "",house.find("div", {"class": "details"}).find("div", {"class": "bedrooms"}).text)
                except Exception as e:
                    logger.warning(f"Failed to parse bedrooms: {e} for house: {address} in {city}")
                    bedrooms = None

                houses.append(
                    House(source=self.name, city=city, address=address, link=self.get_link(path), price=price,
                          available=available, square_meters=square_meters, lat=lat, lon=lon, bedrooms=bedrooms))

        return houses


if __name__ == '__main__':
    asyncio.run(Rebo().crawl())
