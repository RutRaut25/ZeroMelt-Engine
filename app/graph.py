from typing import List, Tuple, Dict, Any
from geopy.distance import geodesic
import numpy as np
import requests
from app.schemas import DarkStoreHub, Order


def get_osrm_route_geometry(coord_start: Tuple[float, float], coord_end: Tuple[float, float]) -> List[List[float]]:
    """
    Fetches real street-level turn-by-turn coordinates between two lat/lon points using OSRM.
    Falls back to straight line if network/API is unreachable.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_start[1]},{coord_start[0]};{coord_end[1]},{coord_end[0]}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and len(data["routes"]) > 0:
                # OSRM returns coordinates as [lon, lat]; flip to [lat, lon] for Folium
                coords = data["routes"][0]["geometry"]["coordinates"]
                return [[lat, lon] for lon, lat in coords]
    except Exception:
        pass
    
    # Fallback to straight line
    return [[coord_start[0], coord_start[1]], [coord_end[0], coord_end[1]]]


def build_spatial_matrices(
    hub: DarkStoreHub,
    orders: List[Order],
    courier_speed_kmh: float = 24.0,
    service_time_per_stop_min: float = 2.0,
) -> Tuple[List[List[int]], List[List[int]], List[Tuple[float, float]]]:
    """
    Builds integer distance matrix (meters) and duration matrix (minutes)
    for the OR-Tools solver. Index 0 is always the DarkStore Hub depot.
    """
    nodes = [(hub.latitude, hub.longitude)] + [(o.latitude, o.longitude) for o in orders]
    num_nodes = len(nodes)
    
    distance_matrix = np.zeros((num_nodes, num_nodes), dtype=int)
    duration_matrix = np.zeros((num_nodes, num_nodes), dtype=int)
    
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i == j:
                continue
            
            dist_km = geodesic(nodes[i], nodes[j]).kilometers
            road_dist_km = dist_km * 1.25
            
            travel_time_min = (road_dist_km / courier_speed_kmh) * 60.0
            service_delay = service_time_per_stop_min if j != 0 else 0.0
            
            distance_matrix[i][j] = int(road_dist_km * 1000)
            duration_matrix[i][j] = int(round(travel_time_min + service_delay))
            
    return distance_matrix.tolist(), duration_matrix.tolist(), nodes