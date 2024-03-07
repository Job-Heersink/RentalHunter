import asyncio
import json
import logging
import re
import traceback


from bs4 import BeautifulSoup, element

from app.database.house import House
from app.sites.base_site import BaseSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Funda(BaseSite):

    def __init__(self):
        super().__init__('https://www.funda.nl', "/zoeken/huur/", end_page=5)

    async def get(self, page=1):
        return (await super().get(url=self.get_link()+f'?search_result={page}&selected_area="[nl]"&sort="date_down"&publication_date=1')).text

    async def crawl_house_for_coordinates(self, house_link):
        response = await super().get(url=house_link)

        if response.status_code == 301 or response.status_code == 302:
            soup = BeautifulSoup(response.text, 'html.parser')
            soup = soup.find("a")
            house_link = soup['href']
            return await self.crawl_house_for_coordinates(self.get_link(house_link))

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
                address = house.find("h2", {"data-test-id": "street-name-house-number"}).text \
                    .replace("\n", "").lstrip().rstrip()
                city_postalcode = house.find("div", {"data-test-id": "postal-code-city"}).text \
                    .replace("\n", "").lstrip().rstrip()
                postal_nr, postal_abc, city = city_postalcode.split(" ", 2)
                postal_code = f"{postal_nr} {postal_abc}"
                available = True
                price = re.sub(r"\D", "", house.find("p", {"data-test-id": "price-rent"}).text)
                square_meters = re.sub(r"\D", "",
                                       house.select("ul[class='mt-1 flex h-6 min-w-0 flex-wrap overflow-hidden']")[
                                           0].contents[0].text)
                if square_meters == "":
                    square_meters = None
                if price == "":
                    return

                lat, lon = await self.crawl_house_for_coordinates(link)
                houses.append(
                    House(source=self.name, city=city, address=address, link=link, price=price,
                          available=available, square_meters=square_meters, postalcode=postal_code,
                          lat=lat, lon=lon))
        except Exception as e:
            logger.error(f"Failed to parse house: {e}")
            traceback.print_exc()

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.find_all("div", {"data-test-id": "search-result-item"})
        if len(houses_page) == 0:
            logger.error(f"Failed to parse {self.name} page {page}. No Houses")

        await asyncio.gather(*[self.crawl_house(house, houses) for house in houses_page])


if __name__ == '__main__':
    res = asyncio.run(Funda().crawl())
    print(f"houses crawled: {len(res)}")
    for h in asyncio.run(Funda().crawl()):
        print(f"{h.address} {h.city}")
