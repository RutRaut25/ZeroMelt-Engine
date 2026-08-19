import time
import requests
from app.schemas import DarkStoreHub, Order, OrderItem, ItemCategory, Courier
from app.solver import ColdChainVRPTSolver
from app.graph import get_osrm_route_geometry
from app.redis_client import FleetSpatialStore

store = FleetSpatialStore()

HUB = DarkStoreHub(hub_id="HUB_01", name="Central Hub", latitude=18.5074, longitude=73.8077)

ORDERS = [
    Order(
        order_id="ORD-104",
        latitude=18.4980, longitude=73.7950,
        earliest_minute=0, latest_minute=15,
        items=[OrderItem(name="Fresh Berry Box", category=ItemCategory.PRODUCE, weight_kg=2.0)]
    ),
    Order(
        order_id="ORD-105",
        latitude=18.5320, longitude=73.8100,
        earliest_minute=0, latest_minute=30,
        items=[OrderItem(name="Snack Pack Box", category=ItemCategory.AMBIENT, weight_kg=0.5)]
    )
]

COURIERS = [Courier(courier_id="RIDER-01", name="Courier #1", max_payload_kg=10.0)]


def run_live_courier_feed():
    print("🚀 Starting Real-Time GPS Telemetry Stream...")
    solver = ColdChainVRPTSolver(hub=HUB, orders=ORDERS, couriers=COURIERS, ambient_temp_c=35.0)
    result = solver.solve()
    
    if not result.routes:
        print("No active routes found.")
        return

    route = result.routes[0]
    full_path_coordinates = []
    
    current_loc = (HUB.latitude, HUB.longitude)
    for stop in route.stops:
        next_loc = (stop.latitude, stop.longitude)
        segment = get_osrm_route_geometry(current_loc, next_loc)
        full_path_coordinates.extend(segment)
        current_loc = next_loc

    # Stream GPS coordinates into Redis store
    for idx, (lat, lon) in enumerate(full_path_coordinates):
        store.update_rider_position(route.courier_id, lat, lon)
        print(f"📡 [RIDER-01] GPS Ping {idx+1}/{len(full_path_coordinates)}: ({lat:.5f}, {lon:.5f})")
        time.sleep(0.5)

    print("🏁 Courier reached final destination!")


if __name__ == "__main__":
    run_live_courier_feed()