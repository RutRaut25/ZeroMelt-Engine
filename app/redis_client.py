import redis
from typing import Optional, Tuple, List, Dict


class FleetSpatialStore:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self._local_cache: Dict[str, Tuple[float, float]] = {}
        try:
            self.r = redis.Redis(
                host=host, port=port, db=db, decode_responses=True, socket_connect_timeout=1.5
            )
            self.r.ping()
            self.available = True
        except (redis.ConnectionError, redis.TimeoutError):
            self.available = False

    def update_rider_position(self, rider_id: str, lat: float, lon: float) -> None:
        """Stores or updates the live GPS coordinates of a delivery rider."""
        if self.available:
            self.r.geoadd("fleet:riders", (lon, lat, rider_id))
        else:
            self._local_cache[rider_id] = (lat, lon)

    def get_rider_position(self, rider_id: str) -> Optional[Tuple[float, float]]:
        """Retrieves latitude and longitude for a given rider."""
        if self.available:
            pos = self.r.geopos("fleet:riders", rider_id)
            if pos and pos[0]:
                lon, lat = pos[0]
                return (float(lat), float(lon))
            return None
        return self._local_cache.get(rider_id)

    def find_nearest_riders(self, lat: float, lon: float, radius_km: float = 3.0) -> List[str]:
        """Finds all couriers within a specific radius of a dark store or customer."""
        if self.available:
            results = self.r.geosearch(
                "fleet:riders",
                longitude=lon,
                latitude=lat,
                radius=radius_km,
                unit="km",
            )
            return results or []
        return list(self._local_cache.keys())