import asyncio
import re

import httpx
from bs4 import BeautifulSoup, element

from app.models.house import House
from app.sites.base_site import BaseSite


class BurgersDijk(BaseSite):

    def __init__(self):
        super().__init__("https://burgersdijk.com", "/huurwoningen/")

    async def get(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.get_link())

        if response.status_code != 200:
            raise Exception(f"Failed to fetch {self.get_link()}: {response.text}")

        return response.text

    async def crawl_page(self, page, houses):
        html = await self.get()
        soup = BeautifulSoup(html, 'html.parser')

        houses_page = soup.find_all("div", {
            "class": "uk-grid uk-grid-small uk-child-width-1-2@s uk-child-width-1-4@l uk-margin"})
        assert len(houses_page) == 1
        houses_page = houses_page[0]

        for house in houses_page.children:
            if type(house) == element.Tag:
                available = len(house.find_all(lambda t: t.name == "div" and "verhuurd" in t.text)) == 0
                path = house.find('a')['href']
                address = house.find("span", {"class": "street-address"}).text.replace("*", "")
                city = house.find("span", {"class": "locality"}).text

                if available:
                    price = house.find("p", {"class": "selling_price"}).text
                    price = re.sub(r"\D", "", price)
                else:
                    price = None

                lat = house.find("span", {"class": "latitude"}).text
                lon = house.find("span", {"class": "longitude"}).text

                square_meters = house.find_all(lambda t: t.name == "p" and "Woonoppervlakte" in t.text)[0].text
                square_meters = float(square_meters.replace("Woonoppervlakte ", "").split(" m")[0])

                houses.append(
                    House(source=self.name, city=city, address=address, link=self.get_link(path), price=price,
                          available=available, square_meters=square_meters, lat=lat, lon=lon))

        return houses


if __name__ == '__main__':
    asyncio.run(BurgersDijk().crawl())
