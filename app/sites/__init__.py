from .alliantie import Alliantie
from .boon import Boon
from .burgersdijk import BurgersDijk
from .domica import Domica
from .funda import Funda
from .house_hunting import HouseHunting
from .ikwilhuren import IkWilHuren
from .nijland import Nijland
from .pararius import Pararius
from .rebo import Rebo

site_list = [BurgersDijk(),
             #Funda(), TODO: Working, but AWS IP ranges are blocked by Funda
             Alliantie(),
             IkWilHuren(),
             Pararius(),
             Rebo(),
             Nijland(),
             Boon(),
             HouseHunting(),
             Domica()]