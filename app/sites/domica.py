import asyncio
import json
import logging
import re
import time

import httpx
from bs4 import BeautifulSoup, element

from app.database.house import House
from app.sites.base_site import BaseSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Nijland(BaseSite):

    def __init__(self):
        super().__init__('https://www.domica.nl/', "/woningaanbod/", end_page=10)

    async def get(self, page=1):
        return (await super().get(url=self.get_link(),
                                  params={"offer": "rent", "sort": "date_asc", "page": page})).text

    async def crawl_page(self, page, houses): #TODO: STILL IMPLEMENT THIS. They do some API calls, so maybe I can do that too
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_res = soup.find("div", {"class": "eazlee_aanbod_widget_container"})
        houses_res = houses_res.find("div", {"class": "eazlee_objects"})
        houses_res = houses_res.find_all("a", recursive=False)
        assert len(houses_res) > 0

        for house in houses_res:
            available = True
            path = house["href"]
            try:
                price = house.find("div", {"class": "eazlee_object_bottom_price"}).text
                price = re.sub(r"\D", "", price)
            except Exception as e:
                logger.warning(f"Failed to parse price: {e} for house: {path}")
                price = None

            address = house.find("div", {"class": "eazlee_object_bottom_street_nummer"}).text
            postal_code, city = house.find("div", {"class": "eazlee_object_bottom_postcode_city"}).text.split(" ", 1)

            houses.append(House(source=self.name, city=city, address=address,
                                link=self.get_link(path), price=price, available=available,
                                square_meters=square_meters, postalcode=postal_code, bedrooms=bedrooms,
                                lat=latitude, lon=longitude))


if __name__ == '__main__':
    asyncio.run(Nijland().crawl())
