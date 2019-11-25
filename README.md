# brother
Python wrapper for getting data from Brother laser and inkjet printers via snmp

## How to use package
```
import asyncio

from pysnmp.hlapi.asyncore.cmdgen import lcd

from brother import Brother

HOST = "brother"


async def main():
    brother = Brother(HOST)
    await brother.update()

    lcd.unconfigure(brother.snmp_engine, None)

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
