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


class Funda(BaseSite):

    def __init__(self):
        super().__init__('https://www.funda.nl', "/zoeken/huur/", end_page=15)

    async def get(self, page=1):
        logger.info(f'fetching page {self.get_link()}?search_result={page}&selected_area=["nl"]')
        async with httpx.AsyncClient() as client:
            response = await client.get(self.get_link(),
                                        params={"search_result": page, "selected_area": '["nl"]', "sort":"date_down"},
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"})

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.get_link()}: {response.text}")

        return response.text

    async def crawl_house_for_coordinates(self, house_link):
        async with httpx.AsyncClient() as client:
            response = await client.get(house_link,
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"})

        if response.status_code == 301:
            soup = BeautifulSoup(response.text, 'html.parser')
            soup = soup.find("a")
            house_link = soup['href']
            return await self.crawl_house_for_coordinates(self.get_link(house_link))

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {house_link}: {response.text}")

        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all("script", {"type": "application/json", "data-object-map-config": ""})
        for s in scripts:
            try:
                jsn = json.loads(s.text)
                if "lat" in jsn and "lng" in jsn:
                    if jsn["lat"] != '' and jsn["lng"] != '':
                        return jsn["lat"], jsn["lng"]
            except Exception as e:
                logger.error(f"Failed to parse house coordinates: {e}")
        return None, None

    async def crawl_house(self, house, houses):
        try:
            if type(house) == element.Tag:
                paths = house.find_all("a", {"class": "h-full"})
                if len(paths) == 0:
                    return
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
                    return

                lat, lon = await self.crawl_house_for_coordinates(link)
                houses.append(
                    House(source=self.name, city=city, address=address, link=link, price=price,
                          available=available, square_meters=square_meters, postalcode=postal_code,
                          lat=lat, lon=lon))
        except Exception as e:
            logger.error(f"Failed to parse house: {e}")
            logger.error(f"on Address: {address}")

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.select("div[class='pt-4']")
        if len(houses_page) == 0:
            raise Exception(f"Failed to parse {self.name} page {page}")

        houses_page = houses_page[0]
        await asyncio.gather(*[self.crawl_house(house, houses) for house in houses_page.children])


if __name__ == '__main__':
    for h in asyncio.run(Funda().crawl()):
        print(h)
