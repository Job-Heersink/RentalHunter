import logging

from app.discord.bot import DiscordBot
from app.handlers.geocoding_handler import get_geocode
from app.database.subscriber import Subscriber, add_subscriber, remove_subscriber
from app.sites import site_list
from app.utils.doc_parser import parse_docstring

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
discord_bot = DiscordBot()


@discord_bot.command("/help")
async def get_help(body):
    """
    Get a list of all commands
    """
    message = "These are the commands that I understand:\n"
    for command, func in discord_bot.commands.items():
        doc = parse_docstring(func.__doc__)
        message += f"- /{command}: {doc['short_description']}\n"
        for param in doc["params"]:
            param_doc = param["doc"].replace('\n', '').rstrip().lstrip()
            message += f"  - {param['name']}: {param_doc}\n"
    return message


@discord_bot.command("/websites")
async def get_websites(body):
    """
    Get a list of all websites that are visited by the bot
    """
    return "These are the websites that I visit every 4 minutes:\n" + "\n".join(
        [f"- {site.name} ({site.url})" for site in site_list])


@discord_bot.command("/subscribe")
async def subscribe(body, min_price: float = None,
                    max_price: float = None,
                    min_rooms: int = None,
                    max_rooms: int = None,
                    min_sqm: float = None,
                    max_sqm: float = None,
                    city: str = None,
                    radius: float = None, ):
    """
    Subscribe to get updates from the bot when a house is found.

    :param min_price: minimum price of the house
    :param max_price: maximum price of the house
    :param min_rooms: minimum amount of rooms
    :param max_rooms: maximum amount of rooms
    :param min_sqm: minimum square meters
    :param max_sqm: maximum square meters
    :param city: city where the house should be located
    :param radius: radius in KM around the city where the house should be located
    """

    # loading kwargs this way allows the bot to parse arguments from the discord command
    kwargs = locals()
    kwargs.pop("body")
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    channel_id = body["channel"]["id"]
    logger.info(f"Subscribing {channel_id} to updates with filters: {kwargs}")
    if city is not None:
        kwargs["city"] = kwargs["city"].capitalize()
        kwargs["latitude"], kwargs["longitude"] = await get_geocode(city=kwargs["city"])

    s = Subscriber(channel_id=channel_id, **kwargs)
    await add_subscriber(s)

    return "\n".join([f"Successfully subscribed! Your filters are:",
                      f"- price from {s.min_price} euro to {s.max_price} euro",
                      f"- square meters from {s.min_sqm} m2 to {s.max_sqm} m2",
                      f"- number of bedrooms from {s.min_rooms} to {s.max_rooms}",
                      f"- city: {s.city} (lat: {s.latitude}, long: {s.longitude})",
                      f"- search radius: {s.radius} km"])


@discord_bot.command("/unsubscribe")
async def unsubscribe(body):
    """
    Unsubscribe from the updates from the bot
    """
    channel_id = body["channel"]["id"]
    await remove_subscriber(channel_id)
    return "Successfully Unsubscribed from the bot."
