from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.schemas import DarkStoreHub, Order, Courier, OptimizationResult
from app.solver import ColdChainVRPTSolver
from app.redis_client import FleetSpatialStore

app = FastAPI(
    title="ZeroMelt Engine API",
    description="Dynamic Cold-Chain Logistics & Thermal VRPTW Optimization Gateway",
    version="1.0.0",
)

spatial_store = FleetSpatialStore()


class DispatchPayload(BaseModel):
    hub: DarkStoreHub
    orders: List[Order]
    couriers: List[Courier]
    ambient_temp_celsius: float = 34.0


@app.get("/")
def root():
    return {
        "engine": "ZeroMelt Dispatch Core",
        "status": "OPERATIONAL",
        "redis_connected": spatial_store.available,
    }


@app.get("/health")
def health_check():
    return {"status": "ONLINE", "redis_available": spatial_store.available}


@app.post("/api/v1/optimize-fleet", response_model=OptimizationResult)
def optimize_fleet(payload: DispatchPayload):
    if not payload.orders:
        raise HTTPException(status_code=400, detail="Order batch cannot be empty.")
    if not payload.couriers:
        raise HTTPException(status_code=400, detail="Active couriers must be greater than zero.")

    solver = ColdChainVRPTSolver(
        hub=payload.hub,
        orders=payload.orders,
        couriers=payload.couriers,
        ambient_temp_c=payload.ambient_temp_celsius,
    )
    return solver.solve()


@app.post("/api/v1/telemetry/rider-location")
def update_location(courier_id: str, lat: float, lon: float):
    spatial_store.update_rider_position(courier_id, lat, lon)
    return {"status": "UPDATED", "courier_id": courier_id, "lat": lat, "lon": lon}


@app.get("/api/v1/telemetry/rider-location/{courier_id}")
def get_location(courier_id: str):
    coords = spatial_store.get_rider_position(courier_id)
    if not coords:
        raise HTTPException(status_code=404, detail="Rider position not found.")
    return {"courier_id": courier_id, "latitude": coords[0], "longitude": coords[1]}