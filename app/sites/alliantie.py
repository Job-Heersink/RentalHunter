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


class Alliantie(BaseSite):

    def __init__(self):
        super().__init__('https://ik-zoek.de-alliantie.nl', "/huren", end_page=4)

    async def get(self, page=1):
        return (await super().get(url=self.get_link()+f'?page={page}')).text

    async def crawl_house(self, house, houses):
        try:
            link = house.find("a")['href']
            info = house.find("div", {"class": "result__info"})
            info_footer = info.find("p", {"class": "result__info__footer"})

            address = info.find("h3").find("span").text
            city = info_footer.find("span", {"class": "city"}).text
            square_meters = re.sub(r"\D", "", info_footer.find("span", {"class": "path"}).text.split(" m2", 1)[0])
            price = re.sub(r"\D", "", info.find("p", {"class": "result__info__price"}).text)
            available = True

            if square_meters == "":
                square_meters = None
            if price == "":
                return

            houses.append(
                House(source=self.name, city=city, address=address, link=link, price=float(price),
                      available=available, square_meters=square_meters))
        except Exception as e:
                logger.error(f"Failed to parse house: {e}")
                traceback.print_exc()

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        html = await self.get(page=page)
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.find_all("div", {"class": "result"})
        if len(houses_page) == 0:
            logger.error(f"Failed to parse {self.name} page {page}. No Houses")

        await asyncio.gather(*[self.crawl_house(house, houses) for house in houses_page])


if __name__ == '__main__':
    res = asyncio.run(Alliantie().crawl())
    print(f"houses crawled: {len(res)}")
    for h in res:
        print(f"{h.address} {h.city}")
