"""Type definitions for Brother."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BrotherSensors:
    """Brother Sensors class."""

    belt_unit_remaining_life: int | None = None
    belt_unit_remaining_pages: int | None = None
    black_counter: int | None = None
    black_drum_counter: int | None = None
    black_drum_remaining_life: int | None = None
    black_drum_remaining_pages: int | None = None
    black_ink_remaining: int | None = None
    black_ink_status: int | None = None
    black_ink: int | None = None
    black_toner_remaining: int | None = None
    black_toner_status: int | None = None
    black_toner: int | None = None
    bw_counter: int | None = None
    color_counter: int | None = None
    cyan_counter: int | None = None
    cyan_drum_counter: int | None = None
    cyan_drum_remaining_life: int | None = None
    cyan_drum_remaining_pages: int | None = None
    cyan_ink_remaining: int | None = None
    cyan_ink_status: int | None = None
    cyan_ink: int | None = None
    cyan_toner_remaining: int | None = None
    cyan_toner_status: int | None = None
    cyan_toner: int | None = None
    drum_counter: int | None = None
    drum_remaining_life: int | None = None
    drum_remaining_pages: int | None = None
    drum_status: int | None = None
    duplex_unit_pages_counter: int | None = None
    fuser_remaining_life: int | None = None
    fuser_unit_remaining_pages: int | None = None
    image_counter: int | None = None
    laser_remaining_life: int | None = None
    laser_unit_remaining_pages: int | None = None
    magenta_counter: int | None = None
    magenta_drum_counter: int | None = None
    magenta_drum_remaining_life: int | None = None
    magenta_drum_remaining_pages: int | None = None
    magenta_ink_remaining: int | None = None
    magenta_ink_status: int | None = None
    magenta_ink: int | None = None
    magenta_toner_remaining: int | None = None
    magenta_toner_status: int | None = None
    magenta_toner: int | None = None
    page_counter: int | None = None
    pf_kit_1_remaining_life: int | None = None
    pf_kit_1_remaining_pages: int | None = None
    pf_kit_mp_remaining_life: int | None = None
    pf_kit_mp_remaining_pages: int | None = None
    status: str | None = None
    uptime: datetime | None = None
    yellow_counter: int | None = None
    yellow_drum_counter: int | None = None
    yellow_drum_remaining_life: int | None = None
    yellow_drum_remaining_pages: int | None = None
    yellow_ink_remaining: int | None = None
    yellow_ink_status: int | None = None
    yellow_ink: int | None = None
    yellow_toner_remaining: int | None = None
    yellow_toner_status: int | None = None
    yellow_toner: int | None = None
