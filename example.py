import asyncio
import logging
from sys import argv

from brother import Brother, SnmpError, UnsupportedModel

# printer IP address/hostname
HOST = "brother"
logging.basicConfig(level=logging.DEBUG)


async def main():
    host = argv[1] if len(argv) > 1 else HOST
    kind = argv[2] if len(argv) > 2 else "laser"

    # argument kind: laser - for laser printer
    #                ink   - for inkjet printer
    brother = Brother(host, kind=kind)

    try:
        await brother.initialize()
        await brother.async_update()
    except (ConnectionError, SnmpError, UnsupportedModel) as error:
        print(f"{error}")
        return

    brother.shutdown()

    if brother.available:
        print(f"Data available: {brother.available}")
        print(f"Model: {brother.model}")
        print(f"Firmware: {brother.firmware}")
        if brother.data.get("status"):
            print(f"Status: {brother.data['status']}")
        print(f"Serial no: {brother.serial}")
        print(f"Sensors data: {brother.data}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
