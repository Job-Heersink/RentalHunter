from app.database.subscriber import get_subscribers
from app.discord.commands import get_help, get_websites, subscribe, unsubscribe


async def test_get_help():
    print(await get_help(None))


async def test_get_websites():
    print(await get_websites(None))


async def test_subscribe():
    print(await subscribe({"channel": {"id": "test"}}))


async def test_unsubscribe():
    """
    Unsubscribe from the updates from the bot
    """
    print(await unsubscribe({"channel": {"id": "test"}}))


async def test_get_subscribers():
    """
    Get a list of all subscribers
    """
    async for subscriber in get_subscribers():
        print(subscriber)

async def batch_test():
    await asyncio.gather(*[unsubscribe({"channel": {"id": f"test_{i}"}}) for i in range(120)])


if __name__ == '__main__':
    import asyncio
    import logging
    logging.basicConfig(level=logging.INFO)

    asyncio.run(batch_test())
