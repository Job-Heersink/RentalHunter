import asyncio
import logging
import re
import time

import httpx
from bs4 import BeautifulSoup, element

from app.models.house import House
from app.sites.base_site import BaseSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pararius(BaseSite):

    def __init__(self):
        super().__init__('https://www.pararius.nl', "/huurwoningen/nederland", end_page=15)

    async def get(self, page=1):
        async with httpx.AsyncClient() as client:
            if page == 1:
                link = self.get_link()
            else:
                link = f"{self.get_link()}/page-{page}"
            response = await client.get(link,
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"})

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.get_link()}: {response.text}")

        return response.text

    def clean_address(self, address):
        if address.startswith("Kamer "):
            address = address[len("Kamer "):]
        elif address.startswith("Appartement "):
            address = address[len("Appartement "):]
        elif address.startswith("Studio "):
            address = address[len("Studio "):]
        elif address.startswith("Huis "):
            address = address[len("Huis "):]
        elif address.startswith("Woning "):
            address = address[len("Woning "):]
        return address

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.select("ul[class='search-list']")
        assert len(houses_page) == 1
        houses_page = houses_page[0]

        for house in houses_page.find_all("li", {"class": "search-list__item--listing"}, recursive=False):
            if type(house) == element.Tag:
                house = house.find("section", recursive=False)
                path = house.find("a", {"class": "listing-search-item__link"})["href"]

                address = house.find("h2", {"class": "listing-search-item__title"}, recursive=False).find("a").text
                address = address.replace("\n", "").lstrip().rstrip()
                address = self.clean_address(address)

                city_details = house.find("div", {"class": "listing-search-item__sub-title'"}, recursive=False).text
                postal_nr, postal_abc, city = city_details.replace("\n", "").lstrip().rstrip().split(" ", 2)
                city = city.split("(")[0].lstrip().rstrip()
                postal_code = f"{postal_nr} {postal_abc}"
                available = True

                try:
                    price = re.sub(r"\D", "", house.find("div", {"class": "listing-search-item__price"}, recursive=False).text)
                    if price == "":
                        raise Exception("No price")
                except Exception as e:
                    logger.warning(f"Failed to parse price: {e} for house: {address} in {city}")
                    price = None
                details = house.find("ul", {"class": "illustrated-features illustrated-features--compact"})
                square_meters = re.sub(r"\D", "", details.find("li", {"class": "illustrated-features__item illustrated-features__item--surface-area"}).text.split("m")[0])
                bedrooms = re.sub(r"\D", "", details.find("li", {"class": "illustrated-features__item illustrated-features__item--number-of-rooms"}).text)
                houses.append(
                    House(source=self.name, city=city, address=address, link=self.get_link(path), price=price,
                          available=available, square_meters=square_meters, postalcode=postal_code, bedrooms=bedrooms))


if __name__ == '__main__':
    asyncio.run(Pararius().crawl())
