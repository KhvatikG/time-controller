from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator
from pydantic.color import Color
from pydantic.dataclasses import dataclass


class Timetable(BaseModel):
    id: int
    open_at: datetime
    close_at: datetime
    day: int
    date: Optional[datetime] = None
    is_working: bool


class Zone(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    delivery_time: int
    transportation_time: int
    cooking_time: int
    price: float
    color: Color | None
    timezone: str
    timezone_own: Optional[str] = None
    free_delivery_count: Optional[int] = None
    free_delivery_price: Optional[float] = None
    minimal_order_price: Optional[float] = None
    area: str | None
    takeaway: bool = False
    priority: int = 0
    rush_price: Optional[float] = None
    rush_free_delivery_price: Optional[float] = None
    rush_delivery_time: Optional[int] = None
    rush_minimal_order_price: Optional[float] = None
    rush_transportation_time: Optional[int] = None
    rush_cooking_time: Optional[int] = None
    rush_delivery_time_expand_minutes: Optional[int] = None
    cooking_time_auto: bool = False
    outsource_reject_from_price: Optional[float] = None
    outsource_subsidy: Optional[float] = None
    outsource_provider: Optional[str] = ""
    outsource_free_delivery_price: Optional[float] = None
    courier_order_fee: Optional[float] = None
    dine_in: bool = False
    service_charge: Optional[float] = None
    fixed_service_charge: Optional[float] = None
    restaurant_id: int
    organization_id: int
    timetables: List[Timetable]

    @field_validator('outsource_provider', mode='before')
    def set_empty_string_provider(cls, v):
        return v or ""  # Default to empty string if None

    class Config:
        use_enum_values = True
        str_strip_whitespace = True
        from_attributes = True


class ZonesList:
    """
    Структура для хранения и работы со списком зон.
    Позволяет получать отдельно зону самовывоза, или все остальные зоны.
    """
    def __init__(self, zones: List[Zone]):
        self.self_delivery_zone: Zone | None = None
        self.delivery_zones: list[Zone] = []
        self.zones: list[Zone] = zones

        for zone in zones:
            if zone.name == "Пункт самовывоза":
                self.self_delivery_zone = zone
            else:
                self.delivery_zones.append(zone)

    def __len__(self) -> int:
        return len(self.zones)

    def __getitem__(self, item) -> Zone:
        return self.zones[item]

    def __contains__(self, item) -> bool:
        return item in self.zones

    def __str__(self) -> str:
        return str(self.zones)

    def __repr__(self) -> str:
        return "ZonesList(" + ",".join(f"{zone.name}" for zone in self.zones) + ")"

    def __eq__(self, other) -> bool:
        return self.zones == other.zones

    def __ne__(self, other) -> bool:
        return self.zones != other.zones

    def get_self_delivery_zone(self) -> Zone:
        return self.self_delivery_zone

    def get_delivery_zones(self) -> list[Zone]:
        return self.delivery_zones

    def append(self, zone: Zone) -> None:
        self.zones.append(zone)
        if zone.name == "Пункт самовывоза":
            self.self_delivery_zone = zone
        else:
            self.delivery_zones.append(zone)
