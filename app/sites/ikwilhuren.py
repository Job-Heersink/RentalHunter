import asyncio
import logging
import re
import time

import httpx
from bs4 import BeautifulSoup, element

from app.database.house import House
from app.sites.base_site import BaseSite

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class IkWilHuren(BaseSite):

    def __init__(self):
        super().__init__('https://ikwilhuren.nu', "/aanbod", end_page=10)

    async def get(self, page=1):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.get_link(),
                                        params={"page": page},
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"})

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.get_link()}: {response.text}")

        return response.text

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.select("div[class='row gy-8']")
        assert len(houses_page) == 1
        houses_page = houses_page[0]

        for house in houses_page.children:
            if type(house) != element.Tag:
                continue

            house = house.find("div", recursive=False)

            img, house = house.find_all("div", recursive=False)
            status = img.find("span", {"class": "badge"}).text
            available = "Te huur" in status

            path = house.find_all("span", recursive=False)[0].find("a")["href"]
            address = house.find_all("span", recursive=False)[0].find("a").text
            address = address.replace("\n", "").lstrip().rstrip()
            postalcode, city = house.find_all("span", recursive=False)[1].text.split(" ", 1)
            house_details = house.find("div", recursive=False)
            price = re.sub(r"\D", "", house_details.find_all("span", recursive=False)[0].text)

            try:
                square_meters = house_details.find_all("span", recursive=False)[1].text
                if "slaapkamer" in square_meters:
                    raise Exception("Not square meters")
                square_meters = re.sub(r"\D", "", square_meters.split("m")[0])
            except Exception as e:
                logger.warning(f"Failed to parse square meters: {e} for house: {address} in {city}")
                square_meters = None

            try:
                bedrooms = re.sub(r"\D", "", house_details.find_all(lambda t: t.name=="span" and "slaapkamer" in t.text)[0].text)
            except Exception as e:
                logger.warning(f"Failed to parse bedrooms: {e} for house: {address} in {city}")
                bedrooms = None

            logger.debug(f"Found house: {address} in {city} for {price} with {square_meters}m2 and {bedrooms} bedrooms")
            houses.append(
                House(source=self.name, city=city, address=address, link=self.get_link(path), price=price,
                      available=available, square_meters=square_meters, postalcode=postalcode, bedrooms=bedrooms))


if __name__ == '__main__':
    asyncio.run(IkWilHuren().crawl())
