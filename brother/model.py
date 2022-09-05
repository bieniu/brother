"""Type definitions for Brother."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class BrotherSensors:
    """Brother Sensors class."""

    model: str
    serial: str
    belt_unit_remaining_life: Optional[int] = None
    belt_unit_remaining_pages: Optional[int] = None
    black_counter: Optional[int] = None
    black_drum_counter: Optional[int] = None
    black_drum_remaining_life: Optional[int] = None
    black_drum_remaining_pages: Optional[int] = None
    black_ink_remaining: Optional[int] = None
    black_ink_status: Optional[int] = None
    black_ink: Optional[int] = None
    black_toner_remaining: Optional[int] = None
    black_toner_status: Optional[int] = None
    black_toner: Optional[int] = None
    bw_counter: Optional[int] = None
    color_counter: Optional[int] = None
    cyan_counter: Optional[int] = None
    cyan_drum_counter: Optional[int] = None
    cyan_drum_remaining_life: Optional[int] = None
    cyan_drum_remaining_pages: Optional[int] = None
    cyan_ink_remaining: Optional[int] = None
    cyan_ink_status: Optional[int] = None
    cyan_ink: Optional[int] = None
    cyan_toner_remaining: Optional[int] = None
    cyan_toner_status: Optional[int] = None
    cyan_toner: Optional[int] = None
    drum_counter: Optional[int] = None
    drum_remaining_life: Optional[int] = None
    drum_remaining_pages: Optional[int] = None
    drum_status: Optional[int] = None
    duplex_unit_pages_counter: Optional[int] = None
    firmware: Optional[str] = None
    fuser_remaining_life: Optional[int] = None
    fuser_unit_remaining_pages: Optional[int] = None
    image_counter: Optional[int] = None
    laser_remaining_life: Optional[int] = None
    laser_unit_remaining_pages: Optional[int] = None
    magenta_counter: Optional[int] = None
    magenta_drum_counter: Optional[int] = None
    magenta_drum_remaining_life: Optional[int] = None
    magenta_drum_remaining_pages: Optional[int] = None
    magenta_ink_remaining: Optional[int] = None
    magenta_ink_status: Optional[int] = None
    magenta_ink: Optional[int] = None
    magenta_toner_remaining: Optional[int] = None
    magenta_toner_status: Optional[int] = None
    magenta_toner: Optional[int] = None
    page_counter: Optional[int] = None
    pf_kit_1_remaining_life: Optional[int] = None
    pf_kit_1_remaining_pages: Optional[int] = None
    pf_kit_mp_remaining_life: Optional[int] = None
    pf_kit_mp_remaining_pages: Optional[int] = None
    status: Optional[str] = None
    uptime: Optional[datetime] = None
    yellow_counter: Optional[int] = None
    yellow_drum_counter: Optional[int] = None
    yellow_drum_remaining_life: Optional[int] = None
    yellow_drum_remaining_pages: Optional[int] = None
    yellow_ink_remaining: Optional[int] = None
    yellow_ink_status: Optional[int] = None
    yellow_ink: Optional[int] = None
    yellow_toner_remaining: Optional[int] = None
    yellow_toner_status: Optional[int] = None
    yellow_toner: Optional[int] = None
