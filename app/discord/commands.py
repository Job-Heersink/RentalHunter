import logging

from app.discord.bot import DiscordBot
from app.handlers.data_handler import get_subscribers, put_subscribers
from app.models.subscriber import Subscriber
from app.sites import site_list
from app.utils.doc_parser import parse_docstring

logger = logging.getLogger(__name__)
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
async def subscribe(body):
    """
    Subscribe to get updates from the bot when a house is found.
    Set a filter to only get updates for houses that match your wishes.
    """
    channel_id = body["channel"]["id"]
    df = await get_subscribers()
    if channel_id in df.index:
        subscription = df.loc[channel_id].to_dict()
        base_response = "You are already subscribed to updates"
    else:
        subscription = Subscriber(channel_id=channel_id).dict()
        df.loc[channel_id] = [subscription[k] for k in df.columns]
        base_response = "Successfully subscribed to the bot"
        await put_subscribers(df)

    return "\n".join([f"{base_response}. Your filters are:",
                      f"- price (min/max): {subscription['price']}",
                      f"- square meters (min/max): {subscription['square_meters']}",
                      f"- bedrooms (min/max): {subscription['bedrooms']}",
                      f"- city: {subscription['city']}",
                      f"- radius: {subscription['radius']}"])


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


@discord_bot.command("/filter")
async def filter_subscription(body, min_price: float = 0, max_price: float = 100000, min_rooms: int = 0,
                              max_rooms: int = 50,
                              min_sqm: int = 0, max_sqm: int = 100000, city: str = "Amsterdam", radius: int = 20):
    """
    Set a filter to only get updates for houses that match your wishes.

    :param min_price: minimum price of the house
    :param max_price: maximum price of the house
    :param min_rooms: minimum amount of rooms
    :param max_rooms: maximum amount of rooms
    :param min_sqm: minimum square meters
    :param max_sqm: maximum square meters
    :param city: city where the house should be located
    :param radius: radius in KM around the city where the house should be located
    """
    logger.info(f"Filtering bot: {body}")
    return "Successfully added the following filters:"
