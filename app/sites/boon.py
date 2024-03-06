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


class Boon(BaseSite):

    def __init__(self):
        super().__init__('https://www.boonmakelaars.nl/', "/huurwoningen/")

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
        houses_res = soup.find("div", {"class": "properties"})
        houses_res = houses_res.find_all("div", {"class": "object"})

        for house in houses_res:
            available = True
            link = house.find("div", {"class": "object-image"}).find("a")["href"]
            address_info = house.find("div", {"class": "object-address"})
            street = address_info.find("span", {"class":"object-street"})
            house_number = address_info.find("span", {"class":"object-housenumber"})
            house_number_addition = address_info.find("span", {"class":"object-housenumber-addition"})
            address = f"{street.text} {house_number.text if house_number is not None else ''} " \
                      f"{house_number_addition.text if house_number_addition is not None else ''}"
            city = address_info.find("span",{"class":"object-place"}).text

            try:
                square_meters = house.find("div", {"class": "object-feature-woonoppervlakte"})\
                    .find("div", {"class": "object-feature-info"}).text.split("m")[0]
                square_meters = re.sub(r"\D", "", square_meters)
                if square_meters == "":
                    raise Exception("No square meters")
            except Exception as e:
                logger.warning(f"Failed to parse square meters: {e} for house: {address} in {city}")
                square_meters = None

            try:
                bedrooms = house.find("div", {"class": "object-feature-aantalkamers"})\
                    .find("div", {"class": "object-feature-info"}).text
                bedrooms = re.sub(r"\D", "", bedrooms)
                if bedrooms == "":
                    raise Exception("No bedrooms")
            except Exception as e:
                logger.warning(f"Failed to parse bedrooms: {e} for house: {address} in {city}")
                bedrooms = None

            houses.append(House(source=self.name, city=city, address=address,
                                link=link, price=None, available=available,
                                square_meters=square_meters, bedrooms=bedrooms))


if __name__ == '__main__':
    for h in asyncio.run(Boon().crawl()):
        print(h)
