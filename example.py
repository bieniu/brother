"""Example for Brother library."""
import asyncio
import logging
from sys import argv

import pysnmp.hlapi.asyncio as hlapi

from brother import Brother, SnmpError, UnsupportedModelError

# printer IP address/hostname
HOST = "brother"
logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    """Run main function."""
    host = argv[1] if len(argv) > 1 else HOST
    printer_type = argv[2] if len(argv) > 2 else "laser"
    # argument printer_type: laser - for laser printer
    #                        ink   - for inkjet printer

    external_snmp = False
    if len(argv) > 3 and argv[3] == "use_external_snmp":
        external_snmp = True

    if external_snmp:
        print("Using external SNMP engine")
        snmp_engine = hlapi.SnmpEngine()
    else:
        snmp_engine = None

    try:
        brother = await Brother.create(
            host, printer_type=printer_type, snmp_engine=snmp_engine
        )
        data = await brother.async_update()
    except (ConnectionError, SnmpError, UnsupportedModelError) as error:
        print(f"{error}")
        return

    brother.shutdown()

    print(f"Model: {brother.model}")
    print(f"MAC address: {brother.mac}")
    print(f"Firmware: {brother.firmware}")
    if data:
        print(f"Status: {data.status}")
        print(f"Serial no: {data.serial}")
        print(f"Sensors data: {data}")


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.close()
