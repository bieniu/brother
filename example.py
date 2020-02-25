import asyncio
from sys import argv

from brother import Brother, SnmpError, UnsupportedModel

# printer IP address/hostname
HOST = "brother"


async def main():
    host = argv[1] if len(argv) > 1 else HOST

    # argument kind: laser - for laser printer
    #                ink   - for inkjet printer
    brother = Brother(host, kind="laser")
    try:
        await brother.async_update()
    except (ConnectionError, SnmpError, UnsupportedModel) as error:
        print(f"{error}")
        return

    if brother.available:
        print(f"Data available: {brother.available}")
        print(f"Model: {brother.model}")
        print(f"Firmware: {brother.firmware}")
        print(f"Status: {brother.data['status']}")
        print(f"Serial no: {brother.serial}")
        print(f"Sensors data: {brother.data}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
