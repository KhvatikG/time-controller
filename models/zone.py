from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator
from pydantic.color import Color


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
    color: Optional[Color] = None
    timezone: str
    timezone_own: Optional[str] = None
    free_delivery_count: Optional[int] = None
    free_delivery_price: Optional[float] = None
    minimal_order_price: Optional[float] = None
    area: Optional[str] = None
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
    Помимо получения всех добавленных в нее зон,
    позволяет получать отдельно зону самовывоза, или все остальные зоны кроме самовывоза.
    """
    def __init__(self, zones: List[Zone]):
        self.self_delivery_zone: Zone | None = None
        self.delivery_zones: list[Zone] = []
        self.all_zones: list[Zone] = zones

        for zone in zones:
            if zone.name == "Пункт самовывоза":
                self.self_delivery_zone = zone
            else:
                self.delivery_zones.append(zone)

    def __len__(self) -> int:
        return len(self.all_zones)

    def __getitem__(self, item) -> Zone:
        return self.all_zones[item]

    def __contains__(self, item) -> bool:
        return item in self.all_zones

    def __str__(self) -> str:
        return str(self.all_zones)

    def __repr__(self) -> str:
        return "ZonesList(" + ",".join(f"{zone.name}" for zone in self.all_zones) + ")"

    def __eq__(self, other) -> bool:
        return self.all_zones == other.all_zones

    def __ne__(self, other) -> bool:
        return self.all_zones != other.all_zones

    def get_self_delivery_zone(self) -> Zone:
        """Получить зону самовывоза"""
        return self.self_delivery_zone

    def get_delivery_zones(self) -> list[Zone]:
        """Получить список зон доставки"""
        return self.delivery_zones

    def get_all_zones(self) -> list[Zone]:
        """Получить список всех зон"""
        return self.all_zones

    def append(self, zone: Zone) -> None:
        """Добавить зону в ZonesList"""
        self.all_zones.append(zone)
        if zone.name == "Пункт самовывоза":
            self.self_delivery_zone = zone
        else:
            self.delivery_zones.append(zone)
