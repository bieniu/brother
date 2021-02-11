"""Constants for Brother Printer library."""
ATTR_CHARSET = "charset"
ATTR_COUNTERS = "counters"
ATTR_FIRMWARE = "firmware"
ATTR_MAINTENANCE = "maintenance"
ATTR_MODEL = "model"
ATTR_NEXTCARE = "nextcare"
ATTR_PAGE_COUNT = "page_counter"
ATTR_SERIAL = "serial"
ATTR_STATUS = "status"
ATTR_UPTIME = "uptime"

VAL_BELT_REMAIN = "belt_unit_remaining_life"
VAL_BELT_REMAIN_PAGES = "belt_unit_remaining_pages"
VAL_BLACK_COUNT = "black_counter"
VAL_BLACK_DRUM_COUNT = "black_drum_counter"
VAL_BLACK_DRUM_REMAIN = "black_drum_remaining_life"
VAL_BLACK_DRUM_REMAIN_PAGES = "black_drum_remaining_pages"
VAL_BLACK_INK = "black_ink"
VAL_BLACK_INK_REMAIN = "black_ink_remaining"
VAL_BLACK_INK_STATUS = "black_ink_status"
VAL_BLACK_TONER = "black_toner"
VAL_BLACK_TONER_REMAIN = "black_toner_remaining"
VAL_BLACK_TONER_STATUS = "black_toner_status"
VAL_BW_COUNT = "b/w_counter"
VAL_COLOR_COUNT = "color_counter"
VAL_CYAN_COUNT = "cyan_counter"
VAL_CYAN_DRUM_COUNT = "cyan_drum_counter"
VAL_CYAN_DRUM_REMAIN = "cyan_drum_remaining_life"
VAL_CYAN_DRUM_REMAIN_PAGES = "cyan_drum_remaining_pages"
VAL_CYAN_INK = "cyan_ink"
VAL_CYAN_INK_REMAIN = "cyan_ink_remaining"
VAL_CYAN_INK_STATUS = "cyan_ink_status"
VAL_CYAN_TONER = "cyan_toner"
VAL_CYAN_TONER_REMAIN = "cyan_toner_remaining"
VAL_CYAN_TONER_STATUS = "cyan_toner_status"
VAL_DRUM_COUNT = "drum_counter"
VAL_DRUM_REMAIN = "drum_remaining_life"
VAL_DRUM_REMAIN_PAGES = "drum_remaining_pages"
VAL_DRUM_STATUS = "drum_status"
VAL_DUPLEX_COUNT = "duplex_unit_pages_counter"
VAL_FUSER_REMAIN = "fuser_remaining_life"
VAL_FUSER_REMAIN_PAGES = "fuser_unit_remaining_pages"
VAL_IMAGE_COUNT = "image_counter"
VAL_LASER_REMAIN = "laser_remaining_life"
VAL_LASER_REMAIN_PAGES = "laser_unit_remaining_pages"
VAL_MAGENTA_COUNT = "magenta_counter"
VAL_MAGENTA_DRUM_COUNT = "magenta_drum_counter"
VAL_MAGENTA_DRUM_REMAIN = "magenta_drum_remaining_life"
VAL_MAGENTA_DRUM_REMAIN_PAGES = "magenta_drum_remaining_pages"
VAL_MAGENTA_INK = "magenta_ink"
VAL_MAGENTA_INK_REMAIN = "magenta_ink_remaining"
VAL_MAGENTA_INK_STATUS = "magenta_ink_status"
VAL_MAGENTA_TONER = "magenta_toner"
VAL_MAGENTA_TONER_REMAIN = "magenta_toner_remaining"
VAL_MAGENTA_TONER_STATUS = "magenta_toner_status"
VAL_PAGE_COUNT = "page_counter"
VAL_PF_1_REMAIN = "pf_kit_1_remaining_life"
VAL_PF_1_REMAIN_PAGES = "pf_kit_1_remaining_pages"
VAL_PF_MP_REMAIN = "pf_kit_mp_remaining_life"
VAL_PF_MP_REMAIN_PAGES = "pf_kit_mp_remaining_pages"
VAL_YELLOW_COUNT = "yellow_counter"
VAL_YELLOW_DRUM_COUNT = "yellow_drum_counter"
VAL_YELLOW_DRUM_REMAIN = "yellow_drum_remaining_life"
VAL_YELLOW_DRUM_REMAIN_PAGES = "yellow_drum_remaining_pages"
VAL_YELLOW_INK = "yellow_ink"
VAL_YELLOW_INK_REMAIN = "yellow_ink_remaining"
VAL_YELLOW_INK_STATUS = "yellow_ink_status"
VAL_YELLOW_TONER = "yellow_toner"
VAL_YELLOW_TONER_REMAIN = "yellow_toner_remaining"
VAL_YELLOW_TONER_STATUS = "yellow_toner_status"

CHARSET_MAP = {"5": "latin2", "2004": "roman8", "8": "cyrillic", "12": "latin5"}

KINDS = ["ink", "laser"]

OIDS_WITHOUT_COUNTERS = {
    ATTR_CHARSET: "1.3.6.1.2.1.43.7.1.1.4.1.1",
    ATTR_FIRMWARE: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.17.0",
    ATTR_MAINTENANCE: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0",
    ATTR_MODEL: "1.3.6.1.4.1.2435.2.3.9.1.1.7.0",
    ATTR_NEXTCARE: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.11.0",
    ATTR_PAGE_COUNT: "1.3.6.1.2.1.43.10.2.1.4.1.1",
    ATTR_SERIAL: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.1.0",
    ATTR_STATUS: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.4.5.2.0",
    ATTR_UPTIME: "1.3.6.1.2.1.1.3.0",
}

OIDS = {**OIDS_WITHOUT_COUNTERS, ATTR_COUNTERS: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.10.0"}

VALUES_COUNTERS = {
    "00": VAL_PAGE_COUNT,
    "01": VAL_BW_COUNT,
    "02": VAL_COLOR_COUNT,
    "06": VAL_DUPLEX_COUNT,
    "12": VAL_BLACK_COUNT,
    "13": VAL_CYAN_COUNT,
    "14": VAL_MAGENTA_COUNT,
    "15": VAL_YELLOW_COUNT,
    "16": VAL_IMAGE_COUNT,
}

VALUES_LASER_MAINTENANCE = {
    "11": VAL_DRUM_COUNT,
    "31": VAL_BLACK_TONER_STATUS,
    "32": VAL_CYAN_TONER_STATUS,
    "33": VAL_MAGENTA_TONER_STATUS,
    "34": VAL_YELLOW_TONER_STATUS,
    "41": VAL_DRUM_REMAIN,
    "63": VAL_DRUM_STATUS,
    "69": VAL_BELT_REMAIN,
    "6a": VAL_FUSER_REMAIN,
    "6b": VAL_LASER_REMAIN,
    "6c": VAL_PF_MP_REMAIN,
    "6d": VAL_PF_1_REMAIN,
    "6f": VAL_BLACK_TONER_REMAIN,
    "70": VAL_CYAN_TONER_REMAIN,
    "71": VAL_MAGENTA_TONER_REMAIN,
    "72": VAL_YELLOW_TONER_REMAIN,
    "73": VAL_CYAN_DRUM_COUNT,
    "74": VAL_MAGENTA_DRUM_COUNT,
    "75": VAL_YELLOW_DRUM_COUNT,
    "7e": VAL_BLACK_DRUM_COUNT,
    "79": VAL_CYAN_DRUM_REMAIN,
    "7a": VAL_MAGENTA_DRUM_REMAIN,
    "7b": VAL_YELLOW_DRUM_REMAIN,
    "80": VAL_BLACK_DRUM_REMAIN,
    "81": VAL_BLACK_TONER,
    "82": VAL_CYAN_TONER,
    "83": VAL_MAGENTA_TONER,
    "84": VAL_YELLOW_TONER,
    "a1": VAL_BLACK_TONER_REMAIN,
    "a2": VAL_CYAN_TONER_REMAIN,
    "a3": VAL_MAGENTA_TONER_REMAIN,
    "a4": VAL_YELLOW_TONER_REMAIN,
}

VALUES_INK_MAINTENANCE = {
    "31": VAL_BLACK_INK_STATUS,
    "32": VAL_CYAN_INK_STATUS,
    "33": VAL_MAGENTA_INK_STATUS,
    "34": VAL_YELLOW_INK_STATUS,
    "6f": VAL_BLACK_INK_REMAIN,
    "70": VAL_CYAN_INK_REMAIN,
    "71": VAL_MAGENTA_INK_REMAIN,
    "72": VAL_YELLOW_INK_REMAIN,
    "81": VAL_BLACK_INK,
    "82": VAL_CYAN_INK,
    "83": VAL_MAGENTA_INK,
    "84": VAL_YELLOW_INK,
    "a1": VAL_BLACK_INK_REMAIN,
    "a2": VAL_CYAN_INK_REMAIN,
    "a3": VAL_MAGENTA_INK_REMAIN,
    "a4": VAL_YELLOW_INK_REMAIN,
}

VALUES_LASER_NEXTCARE = {
    "73": VAL_LASER_REMAIN_PAGES,
    "77": VAL_PF_1_REMAIN_PAGES,
    "82": VAL_DRUM_REMAIN_PAGES,
    "86": VAL_PF_MP_REMAIN_PAGES,
    "88": VAL_BELT_REMAIN_PAGES,
    "89": VAL_FUSER_REMAIN_PAGES,
    "a4": VAL_BLACK_DRUM_REMAIN_PAGES,
    "a5": VAL_CYAN_DRUM_REMAIN_PAGES,
    "a6": VAL_MAGENTA_DRUM_REMAIN_PAGES,
    "a7": VAL_YELLOW_DRUM_REMAIN_PAGES,
}

PERCENT_VALUES = [
    VAL_BELT_REMAIN,
    VAL_BLACK_DRUM_REMAIN,
    VAL_BLACK_INK_REMAIN,
    VAL_BLACK_TONER_REMAIN,
    VAL_CYAN_DRUM_REMAIN,
    VAL_CYAN_INK_REMAIN,
    VAL_CYAN_TONER_REMAIN,
    VAL_DRUM_REMAIN,
    VAL_FUSER_REMAIN,
    VAL_LASER_REMAIN,
    VAL_MAGENTA_DRUM_REMAIN,
    VAL_MAGENTA_INK_REMAIN,
    VAL_MAGENTA_TONER_REMAIN,
    VAL_PF_1_REMAIN,
    VAL_PF_MP_REMAIN,
    VAL_YELLOW_DRUM_REMAIN,
    VAL_YELLOW_INK_REMAIN,
    VAL_YELLOW_TONER_REMAIN,
]

OIDS_HEX = [OIDS[ATTR_COUNTERS], OIDS[ATTR_MAINTENANCE], OIDS[ATTR_NEXTCARE]]
