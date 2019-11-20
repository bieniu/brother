import asyncio

from brother import Brother

HOST = "brother"


async def main():
    brother = Brother(HOST)
    await brother.update()

    data = brother.data
    available = brother.available

    if available:
        print(f"Data available: {available}")
        print(data)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
