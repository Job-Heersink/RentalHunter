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


class HouseHunting(BaseSite):

    def __init__(self):
        super().__init__('https://househunting.nl/', "/wp-json/houses/posts", end_page=15)

    async def get(self, page=1):
        async with httpx.AsyncClient() as client:
            form = {"km": "", "t": "320243", "page": page, "sort": ""}
            response = await client.post(self.get_link(),
                                         data=form,
                                         headers={
                                             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
                                             "Host": "househunting.nl",
                                             "Origin": "https://househunting.nl",
                                             "Referer": "https://househunting.nl/woningaanbod/",
                                             "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.get_link()}: {response.text}")

        return response.json()

    async def crawl_house(self, house, houses):
        try:
            available = True
            address = house["title"]
            city = house["city"]
            url = house["url"]
            price = house["price"]
            square_meters = None
            bedrooms = None

            async with httpx.AsyncClient() as client:
                response = await client.get(url,
                                            headers={
                                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"})
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch {url}: {response.text}")

                soup = BeautifulSoup(response.text, 'html.parser')

            details = soup.find("ul", {"class": "details"})
            for detail in details.find_all("li"):
                if "Oppervlakte" in detail.text:
                    square_meters = re.sub(r"\D", "", detail.text.split("m")[0])
                if "Kamers" in detail.text:
                    bedrooms = re.sub(r"\D", "", detail.text)

            latitude, longitude = None, None
            try:
                maps = soup.find("div", {"class": "google-map"}).find("div", {"class": "marker"})
                latitude, longitude = maps["data-lat"], maps["data-lng"]
            except Exception as e:
                logger.warning(f"Failed to parse coordinates: {e} for house: {address} in {city}")

            houses.append(House(source=self.name, city=city, address=address,
                                link=url, price=price, available=available,
                                square_meters=square_meters, postalcode=None, bedrooms=bedrooms,
                                lat=latitude, lon=longitude))
        except Exception as e:
            logger.error(f"Failed to parse house: {e}")

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        jsn = await self.get(page=page)
        await asyncio.gather(*[self.crawl_house(house, houses) for house in jsn["posts"]])


if __name__ == '__main__':
    for h in asyncio.run(HouseHunting().crawl()):
        print(h)
