import asyncio
import logging

import numpy as np
import pandas as pd

from app.database.house import House
from app.database.subscriber import Subscriber, get_subscribers
from app.discord.commands import discord_bot

logger = logging.getLogger(__name__)


class UnicodeEmotes:
    house = "🏠"
    city = "🌆"
    money = "💰"
    bed = "🛏️"
    ruler = "📏"
    globe = "🌍"


async def _notify_subscriber(sub: Subscriber, df: pd.DataFrame):
    logger.info(f"Notifying {sub.channel_id} about new houses")
    filtered_houses = df.loc[
        ((df["price"] >= sub.min_price) | df["price"].isnull()) &
        ((df["price"] <= sub.max_price) | df["price"].isnull()) &
        ((df["bedrooms"] >= sub.min_rooms) | df["bedrooms"].isnull()) &
        ((df["bedrooms"] <= sub.max_rooms) | df["bedrooms"].isnull()) &
        ((df["square_meters"] >= sub.min_sqm) | df["square_meters"].isnull()) &
        ((df["square_meters"] <= sub.max_sqm) | df["square_meters"].isnull()) &
        ((np.absolute(df["lon"] - sub.longitude) <= np.absolute(sub.radius / (111.320 * np.cos(sub.latitude*(np.pi/180))))) | df[
            "lon"].isnull()) &
        ((np.absolute(df["lat"] - sub.latitude) <= np.absolute(sub.radius / 110.574)) | df["lat"].isnull())
        ]

    logger.info(f"Found {len(filtered_houses)} houses for {sub.channel_id}")
    filtered_houses = filtered_houses.copy().replace({np.nan: None})
    for i, h in filtered_houses.iterrows():
        house = House(address=i, **h.to_dict())
        await discord_bot.send_message(
            f"""We found a house for you!!
City {UnicodeEmotes.city}: {house.city}
Address {UnicodeEmotes.house}: {house.address}
Price {UnicodeEmotes.money}: {house.price}
Rooms {UnicodeEmotes.bed}: {house.bedrooms if house.bedrooms is not None else "Unknown"}
Square meters {UnicodeEmotes.ruler}: {house.square_meters if house.square_meters is not None else "Unknown"}
Link {UnicodeEmotes.globe}: {house.link}
            """, sub.channel_id)


async def notify_subscribers(houses):
    notify_tasks = []
    if len(houses) == 0:
        return
    df = pd.DataFrame([h.dict() for h in houses])
    df = df.set_index("address")
    async for s in get_subscribers():
        notify_tasks.append(asyncio.create_task(_notify_subscriber(s, df)))
    await asyncio.gather(*notify_tasks)
