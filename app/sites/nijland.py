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
        super().__init__('https://www.nijland.nl/', "/aanbod/woningaanbod/+500km/huur/aantal-80/")

    async def get(self, page=1):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.get_link(),
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"})

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.get_link()}: {response.text}")

        return response.text

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_res = soup.find_all("li", {"class": "aanbodEntry"})
        for house in houses_res:
            available = True

            jsn = house.find("script", {"type": "application/ld+json"}).text
            jsn = json.loads(jsn)
            address = jsn["address"]["streetAddress"]
            postal_code = jsn["address"]["postalCode"]
            city = jsn["address"]["addressLocality"]
            longitude = jsn["geo"]["longitude"]
            latitude = jsn["geo"]["latitude"]
            path = jsn["url"]

            try:
                price = house.find("span", {"class": "huurprijs"}).find("span", {"class": "kenmerkValue"}).text
                price = re.sub(r"\D", "", price)
                if price == "":
                    raise Exception("No price")
            except Exception as e:
                logger.warning(f"Failed to parse price: {e} for house: {address} in {city}")
                price = None

            try:
                square_meters = \
                house.find("span", {"class": "inhoud"}).find("span", {"class": "kenmerkValue"}).text.split("m")[0]
                square_meters = re.sub(r"\D", "", square_meters)
                if square_meters == "":
                    raise Exception("No square meters")
            except Exception as e:
                logger.warning(f"Failed to parse square meters: {e} for house: {address} in {city}")
                square_meters = None

            try:
                bedrooms = house.find("span", {"class": "aantalkamers"}).find("span", {"class": "kenmerkValue"}).text
                bedrooms = re.sub(r"\D", "", bedrooms)
                if bedrooms == "":
                    raise Exception("No bedrooms")
            except Exception as e:
                logger.warning(f"Failed to parse bedrooms: {e} for house: {address} in {city}")
                bedrooms = None

            houses.append(House(source=self.name, city=city, address=address,
                                link=self.get_link(path), price=price, available=available,
                                square_meters=square_meters, postalcode=postal_code, bedrooms=bedrooms,
                                lat=latitude, lon=longitude))


if __name__ == '__main__':
    asyncio.run(Nijland().crawl())
