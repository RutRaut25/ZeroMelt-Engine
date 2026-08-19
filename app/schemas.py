from enum import Enum
from typing import List, Dict
from pydantic import BaseModel, Field


class ItemCategory(str, Enum):
    FROZEN = "frozen"        # Ice cream, frozen meat, gelato
    CHILLED = "chilled"      # Raw milk, fresh poultry, yogurt
    PRODUCE = "produce"      # Fresh berries, vegetables
    AMBIENT = "ambient"      # Dry goods, snacks, room temp items


class OrderItem(BaseModel):
    name: str
    category: ItemCategory
    weight_kg: float = Field(..., gt=0.0, description="Weight in kilograms")


class Order(BaseModel):
    order_id: str
    latitude: float
    longitude: float
    items: List[OrderItem]
    earliest_minute: int = 0
    latest_minute: int = 30
    min_quality_threshold: float = Field(default=0.80, ge=0.0, le=1.0)


class DarkStoreHub(BaseModel):
    hub_id: str
    name: str
    latitude: float
    longitude: float


class Courier(BaseModel):
    courier_id: str
    name: str
    max_payload_kg: float = 12.0
    speed_kmh: float = 24.0


class RouteStop(BaseModel):
    order_id: str
    latitude: float
    longitude: float
    arrival_minute: float
    departure_minute: float
    quality_indices: Dict[str, float]
    is_safe: bool


class CourierRoute(BaseModel):
    courier_id: str
    courier_name: str
    stops: List[RouteStop]
    total_distance_km: float
    total_duration_minutes: float
    total_load_kg: float
    spoilage_count: int


class OptimizationResult(BaseModel):
    status: str
    routes: List[CourierRoute]
    unassigned_orders: List[str]
    total_distance_km: float
    fleet_spoilage_rate_pct: float
    ambient_temp_celsius: float