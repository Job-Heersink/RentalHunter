import logging

from app.discord.bot import DiscordBot
from app.handlers.data_handler import get_subscribers, put_subscribers
from app.handlers.geocoding_handler import get_geocode
from app.models.subscriber import Subscriber
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
    return "These are the websites that I visit every 10 minutes:\n" + "\n".join(
        [f"- {site.name}" for site in site_list])


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
    df = await get_subscribers()
    if city is not None:
        kwargs["city"] = kwargs["city"].capitalize()
        kwargs["latitude"], kwargs["longitude"] = await get_geocode(city=kwargs["city"])

    if channel_id in df.index:
        subscription = df.loc[channel_id].to_dict()
        subscription.update(kwargs)
        df.loc[channel_id] = [subscription[k] for k in df.columns]
        base_response = "You are already subscribed to updates"
    else:
        subscription = Subscriber(channel_id=channel_id, **kwargs).dict()
        df.loc[channel_id] = [subscription[k] for k in df.columns]
        base_response = "Successfully subscribed to the bot"
        await put_subscribers(df)

    return "\n".join([f"{base_response}. Your filters are:",
                      f"- price from {subscription['min_price']} euro to {subscription['max_price']} euro",
                      f"- square meters from {subscription['min_sqm']} m2 to {subscription['max_sqm']} m2",
                      f"- number of bedrooms from {subscription['min_rooms']} to {subscription['max_rooms']}",
                      f"- city: {subscription['city']} (long: {subscription['latitude']}, lat: {subscription['longitude']})",
                      f"- search radius: {subscription['radius']} km"])


@discord_bot.command("/unsubscribe")
async def unsubscribe(body):
    """
    Unsubscribe from the updates from the bot
    """
    channel_id = body["channel"]["id"]
    df = await get_subscribers()
    if channel_id in df.index:
        df = df.drop(channel_id)
        await put_subscribers(df)
        return "Successfully Unsubscribed from the bot."
    else:
        return "Cannot Unsubscribe. You are not subscribed to the bot."
