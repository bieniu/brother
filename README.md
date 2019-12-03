# brother
Python wrapper for getting data from Brother laser and inkjet printers via snmp

## How to use package
```py
import asyncio

from brother import Brother, SnmpError, UnsupportedModel

# printer IP address/hostname
HOST = "192.172.10.12"


async def main():
    # argument kind: laser - for laser printer
    #                ink   - for inkjet printer
    brother = Brother(HOST, kind="laser")
    try:
        await brother.update()
    except (SnmpError, UnsupportedModel) as error:
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
```
