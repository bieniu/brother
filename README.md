[![GitHub Release][releases-shield]][releases]
[![PyPI][pypi-releases-shield]][pypi-releases]
[![PyPI - Downloads][pypi-downloads]][pypi-statistics]
[![Buy me a coffee][buy-me-a-coffee-shield]][buy-me-a-coffee]
[![PayPal_Me][paypal-me-shield]][paypal-me]

# brother
Python wrapper for getting data from Brother laser and inkjet printers via snmp

## How to use package
```py
import asyncio
from sys import argv

from brother import Brother, SnmpError, UnsupportedModel

# printer IP address/hostname
import asyncio
import logging
from sys import argv

import pysnmp.hlapi.asyncio as hlapi

from brother import Brother, SnmpError, UnsupportedModel

# printer IP address/hostname
HOST = "brother"
logging.basicConfig(level=logging.DEBUG)


async def main():
    host = argv[1] if len(argv) > 1 else HOST
    kind = argv[2] if len(argv) > 2 else "laser"
    # argument kind: laser - for laser printer
    #                ink   - for inkjet printer

    external_snmp = False
    if len(argv) > 3 and argv[3] == "use_external_snmp":
        external_snmp = True

    if external_snmp:
        print("Using external SNMP engine")
        snmp_engine = hlapi.SnmpEngine()
        brother = Brother(host, kind=kind, snmp_engine=snmp_engine)
    else:
        brother = Brother(host, kind=kind)

    try:
        data = await brother.async_update()
    except (ConnectionError, SnmpError, UnsupportedModel) as error:
        print(f"{error}")
        return

    brother.shutdown()

    print(f"Model: {brother.model}")
    print(f"Firmware: {brother.firmware}")
    if data:
        print(f"Status: {data.status}")
        print(f"Serial no: {data.serial}")
        print(f"Sensors data: {data}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```
[releases]: https://github.com/bieniu/brother/releases
[releases-shield]: https://img.shields.io/github/release/bieniu/brother.svg?style=popout
[pypi-releases]: https://pypi.org/project/brother/
[pypi-statistics]: https://pepy.tech/project/brother
[pypi-releases-shield]: https://img.shields.io/pypi/v/brother
[pypi-downloads]: https://pepy.tech/badge/brother/month
[buy-me-a-coffee-shield]: https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white
[buy-me-a-coffee]: https://www.buymeacoffee.com/QnLdxeaqO
[paypal-me-shield]: https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal
[paypal-me]: https://www.paypal.me/bieniu79
