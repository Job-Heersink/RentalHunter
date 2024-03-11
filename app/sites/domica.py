import asyncio
import logging

from app.database.house import House
from app.sites.base_site import BaseSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Domica(BaseSite):

    def __init__(self):
        super().__init__('https://www.domica.nl/',
                         "/rts/collections/public/3d202c54/runtime/collection/EAZLEE/data",
                         end_page=1)

    async def get(self, page=1):
        return (await super().get(url=self.get_link(),
                                  params={"page": {"pageSize": 100, "pageNumber": 0},
                                          "filters": [{"field": "division", "operator": "eq", "value": "property"},
                                                      {"field": "tmp_label", "operator": "NIN", "value": ["*"]},
                                                      {"field": "tmp_forrent", "operator": "EQ", "value": "1"},
                                                      {"field": "tmp_city", "operator": "NE", "value": "*"},
                                                      {"field": "tmp_streetAddress", "operator": "NE", "value": "*"},
                                                      {"field": "tmp_property_type_1", "operator": "NE", "value": "*"},
                                                      {"field": "tmp_property_type_2", "operator": "NE", "value": "*"},
                                                      {"field": "tmp_property_type_3", "operator": "NE", "value": "*"},
                                                      {"field": "tmp_num_bedrooms", "operator": "GTE", "value": "0"},
                                                      {"field": "tmp_interior", "operator": "NE", "value": "*"},
                                                      {"field": "tmp_surface", "operator": "GTE", "value": "0"},
                                                      {"field": "tmp_price", "operator": "GTE", "value": "0"},
                                                      {"field": "tmp_price", "operator": "GTE", "value": "0"},
                                                      {"field": "po-api", "operator": "NE", "value": "*"}
                                                      ],
                                          "sortBy": {"field": "ranking", "direction": "asc"},
                                          "language": "DUTCH"})).json()

    async def crawl_page(self, page, houses):
        logger.info(f"crawling page {page}")
        result = await self.get(page=page)
        res_houses = result['values']
        for house in res_houses:
            available = True
            path = f"/woning/{house['page_item_url']}"
            house_data = house["data"]
            city = house_data['city']
            price = house_data.get('price', None)
            square_meters = house_data.get('surface', None)
            bedrooms = house_data.get('num_bedrooms', None)
            if bedrooms == 0:
                bedrooms = None

            loc_data = house_data.get('locality', {'street':None, 'number':None,
                                                   'lat':None, 'lng':None, 'zipcode':None})
            address = f"{loc_data.get('street', None)} {loc_data.get('number', None)}"
            latitude = loc_data.get('lat', None)
            longitude = loc_data.get('lng', None)
            postal_code = loc_data.get('zipcode', None)
            houses.append(House(source=self.name, city=city, address=address, link=self.get_link(path),
                                price=price, available=available, square_meters=square_meters, postalcode=postal_code,
                                bedrooms=bedrooms, lat=latitude, lon=longitude))


if __name__ == '__main__':
    for _h in asyncio.run(Domica().crawl()):
        print(_h)
