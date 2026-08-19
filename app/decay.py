import math
from app.schemas import ItemCategory, OrderItem

# Degradation rate constants (k) per item category
DECAY_COEFFICIENTS = {
    ItemCategory.FROZEN: 0.085,    # Melts rapidly in minutes
    ItemCategory.CHILLED: 0.035,   # Spoils moderately
    ItemCategory.PRODUCE: 0.012,   # Slow decay
    ItemCategory.AMBIENT: 0.001,   # Negligible decay
}

REFERENCE_TEMP_C = 25.0


def calculate_quality(
    item: OrderItem,
    transit_time_minutes: float,
    ambient_temp_celsius: float = 34.0,
    initial_quality: float = 1.0,
) -> float:
    """
    Calculates remaining freshness Q(t) in [0.0, 1.0].
    Formula: Q(t) = Q0 * exp( -k * (T_amb / T_ref) * t )
    """
    k = DECAY_COEFFICIENTS.get(item.category, 0.01)
    thermal_multiplier = max(0.5, ambient_temp_celsius / REFERENCE_TEMP_C)
    
    decay_exponent = -k * thermal_multiplier * transit_time_minutes
    current_quality = initial_quality * math.exp(decay_exponent)
    
    return max(0.0, min(1.0, round(current_quality, 4)))


def compute_max_safe_transit_time(
    item: OrderItem,
    ambient_temp_celsius: float,
    min_quality_threshold: float = 0.80,
) -> float:
    """
    Derives the hard deadline (in minutes) before an item breaches its freshness floor.
    Formula: t_safe = -ln(Q_min) / (k * (T / T_ref))
    """
    k = DECAY_COEFFICIENTS.get(item.category, 0.01)
    thermal_multiplier = max(0.5, ambient_temp_celsius / REFERENCE_TEMP_C)
    
    if min_quality_threshold <= 0:
        return 999.0
    
    max_minutes = -math.log(min_quality_threshold) / (k * thermal_multiplier)
    return round(max_minutes, 2)