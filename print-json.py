"""Tool to print out stats to stdout as json."""

import asyncio
import json
import logging
from sys import argv

from brother import Brother, SnmpError, UnsupportedModelError, BrotherSensors

# printer IP address/hostname
HOST = "brother"
logging.basicConfig(level=logging.WARNING)

# Define a custom DTO and encoding to JSON
class JsonData:
    def __init__(self, brother, data):
        self.brother = brother
        self.data = data

def del_none(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.

    This alters the input so you may wish to ``copy`` the dict first.
    """
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            del_none(value)
    return d  # For convenience

def encode_object(obj):
    if isinstance(obj, JsonData):
        # product JSON object for the main members and add
        # "data" as a nested object
        return {'model': obj.brother.model,
                'mac': obj.brother.mac,
                'firmware': obj.brother.firmware,
                'serial': obj.brother.serial,
                'data': obj.data}
    elif isinstance(obj, BrotherSensors):
        # use __dict__ to not have to list all the members here
        dict__ = obj.__dict__

        # replace datetime with string to avoid errors when converting
        dict__["uptime"] = dict__["uptime"].strftime("%Y-%m-%dT%H:%M:%SZ")

        # make resulting JSON compact by excluding unset values
        del_none(dict__)

        # finally create json string and parse it into a JSON object
        return json.loads(json.dumps(dict__))

    return obj

async def main() -> None:
    """Run main function."""
    host = argv[1] if len(argv) > 1 else HOST
    printer_type = argv[2] if len(argv) > 2 else "laser"
    # argument printer_type: laser - for laser printer
    #                        ink   - for inkjet printer

    try:
        brother = await Brother.create(
            host,
            port=161,
            community="public",
            printer_type=printer_type,
        )
        data = await brother.async_update()
    except (ConnectionError, SnmpError, TimeoutError, UnsupportedModelError) as error:
        print(f"{error}")
        return

    brother.shutdown()

    json_data= JsonData(brother, data)

    print(json.dumps(json_data, indent=2, default=encode_object))

loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.close()
