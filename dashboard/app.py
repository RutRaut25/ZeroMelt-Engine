import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from app.schemas import DarkStoreHub, Order, OrderItem, ItemCategory, Courier
from app.solver import ColdChainVRPTSolver
from app.graph import get_osrm_route_geometry
from app.redis_client import FleetSpatialStore

st.set_page_config(
    page_title="ZeroMelt Engine | Dispatch Control",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Modern Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Background adjustments */
    .stApp {
        background-color: #0b0f19;
    }
    
    /* Sleek KPI Cards */
    .kpi-container {
        background: linear-gradient(180deg, #161f30 0%, #0f172a 100%);
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-container:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        margin-top: 4px;
        color: #f8fafc;
        display: flex;
        align-items: baseline;
        gap: 6px;
    }
    .kpi-sub {
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* Status Badges */
    .badge-hub {
        background: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    /* Section Wrappers */
    .panel-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Controls ---
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <span style="font-size: 2rem;">🧊</span>
        <div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; line-height: 1.1;">ZeroMelt</div>
            <div style="font-size: 0.75rem; color: #38bdf8; font-weight: 600;">DISPATCH CORE v1.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Thermal-aware real-time dynamic routing solver")
    st.divider()
    
    ambient_temp = st.slider("🌡️ Ambient Temperature (°C)", min_value=15.0, max_value=45.0, value=35.0, step=1.0)
    num_couriers = st.slider("🚴 Available Couriers", min_value=1, max_value=4, value=2)
    payload_cap = st.number_input("📦 Courier Payload Limit (kg)", value=10.0, step=1.0)
    
    st.divider()
    st.markdown("<div class='badge-hub'>📍 ACTIVE ZONE: PUNE CENTRAL</div>", unsafe_allow_html=True)
    st.caption("Depot: Kothrud Hub • Geofenced Radius: 8.0 km")

# Central Hub Depot
HUB = DarkStoreHub(hub_id="HUB_01", name="Pune Central DarkStore", latitude=18.5074, longitude=73.8077)

# Batch Orders
MOCK_ORDERS = [
    Order(order_id="ORD-101", latitude=18.5145, longitude=73.8180, earliest_minute=0, latest_minute=20, items=[OrderItem(name="Belgian Chocolate Tub", category=ItemCategory.FROZEN, weight_kg=0.8)]),
    Order(order_id="ORD-102", latitude=18.5250, longitude=73.8300, earliest_minute=0, latest_minute=30, items=[OrderItem(name="Organic Milk 1L", category=ItemCategory.CHILLED, weight_kg=1.0)]),
    Order(order_id="ORD-103", latitude=18.5020, longitude=73.8250, earliest_minute=0, latest_minute=25, items=[OrderItem(name="Fresh Chicken Breasts", category=ItemCategory.CHILLED, weight_kg=1.2)]),
    Order(order_id="ORD-104", latitude=18.4980, longitude=73.7950, earliest_minute=0, latest_minute=15, items=[OrderItem(name="Strawberries Box", category=ItemCategory.PRODUCE, weight_kg=2.0)]),
    Order(order_id="ORD-105", latitude=18.5320, longitude=73.8100, earliest_minute=0, latest_minute=30, items=[OrderItem(name="Party Snack Pack", category=ItemCategory.AMBIENT, weight_kg=0.5)]),
    Order(order_id="ORD-106", latitude=18.5190, longitude=73.7910, earliest_minute=0, latest_minute=18, items=[OrderItem(name="Vanilla Bean Gelato", category=ItemCategory.FROZEN, weight_kg=0.7)])
]

COURIERS = [Courier(courier_id=f"RIDER-0{i+1}", name=f"Courier #{i+1}", max_payload_kg=payload_cap) for i in range(num_couriers)]

# Run Solver
solver = ColdChainVRPTSolver(hub=HUB, orders=MOCK_ORDERS, couriers=COURIERS, ambient_temp_c=ambient_temp)
results = solver.solve()
spatial_store = FleetSpatialStore()

# --- Main Dashboard Header ---
head_col, status_col = st.columns([3, 1])
with head_col:
    st.markdown("<h1 style='color: #f8fafc; margin-bottom: 0px;'>🧊 ZeroMelt Control Center</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.95rem; margin-top: 4px;'>Dynamic Cold-Chain Logistics & Thermal VRPTW Optimization Core</p>", unsafe_allow_html=True)

# --- KPI Status Row ---
k1, k2, k3, k4 = st.columns(4)

with k1:
    status_color = "#34d399" if results.status == "OPTIMAL" else "#fbbf24"
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Solver Status</div>
        <div class="kpi-value" style="color: {status_color};">{results.status}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Total Distance</div>
        <div class="kpi-value">{results.total_distance_km} <span class="kpi-sub" style="color: #64748b;">KM</span></div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    spoil_color = "#34d399" if results.fleet_spoilage_rate_pct == 0 else "#f87171"
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Fleet Spoilage Rate</div>
        <div class="kpi-value" style="color: {spoil_color};">{results.fleet_spoilage_rate_pct}% <span class="kpi-sub" style="color: #34d399;">(Protected)</span></div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    temp_color = "#f87171" if ambient_temp >= 35 else "#38bdf8"
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Ambient Weather</div>
        <div class="kpi-value" style="color: {temp_color};">{ambient_temp}°C <span class="kpi-sub" style="color: #64748b;">Live</span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Dispatch Context Alert ---
if results.status == "PARTIAL":
    st.warning(f"⚠️ **Thermal Constraint Active:** At **{ambient_temp}°C**, frozen items cannot meet freshness criteria with **{num_couriers} couriers**. Unserviced orders were safely held to maintain 0.0% Spoilage. Increase couriers or reduce temperature to clear full backlog.")
else:
    st.success(f"✅ **Optimal Fleet Sync:** All perishable orders safely scheduled with 100% quality retention.")

# --- Viewport: Map & Telemetry ---
col_map, col_telemetry = st.columns([1.5, 1], gap="large")

with col_map:
    st.markdown("### 🗺️ Dispatched Road Geometry (OSRM)")
    
    m = folium.Map(location=[HUB.latitude, HUB.longitude], zoom_start=13, tiles="CartoDB dark_matter")
    
    # Hub Depot Marker
    folium.Marker(
        [HUB.latitude, HUB.longitude],
        popup=f"<b>Depot:</b> {HUB.name}",
        icon=folium.Icon(color="white", icon_color="black", icon="home", prefix="fa"),
    ).add_to(m)
    
    ROUTE_PALETTE = ["#38bdf8", "#34d399", "#a855f7", "#fb923c"]
    
    for c_idx, route in enumerate(results.routes):
        route_color = ROUTE_PALETTE[c_idx % len(ROUTE_PALETTE)]
        current_loc = (HUB.latitude, HUB.longitude)
        
        for stop in route.stops:
            next_loc = (stop.latitude, stop.longitude)
            segment = get_osrm_route_geometry(current_loc, next_loc)
            folium.PolyLine(segment, color=route_color, weight=4, opacity=0.9, tooltip=f"{route.courier_name} Path").add_to(m)
            current_loc = next_loc
            
            icon_color = "green" if stop.is_safe else "red"
            freshness_text = "<br>".join([f"• {name}: <b>{int(score*100)}%</b>" for name, score in stop.quality_indices.items()])
            
            popup_html = f"""
            <div style='font-family: sans-serif; font-size: 12px; color: #1e293b;'>
                <b>Order:</b> {stop.order_id}<br>
                <b>Courier:</b> {route.courier_name}<br>
                <b>Arrival ETA:</b> {stop.arrival_minute:.1f} mins<br>
                <b>Freshness Status:</b><br>{freshness_text}
            </div>
            """
            folium.Marker(
                [stop.latitude, stop.longitude],
                popup=popup_html,
                icon=folium.Icon(color=icon_color, icon="shopping-cart", prefix="fa"),
            ).add_to(m)
            
        # Return path
        return_geom = get_osrm_route_geometry(current_loc, (HUB.latitude, HUB.longitude))
        folium.PolyLine(return_geom, color=route_color, weight=2, opacity=0.5, dash_array="6, 8").add_to(m)
        
        # Live Rider GPS
        live_gps = spatial_store.get_rider_position(route.courier_id)
        if live_gps:
            folium.Marker(
                [live_gps[0], live_gps[1]],
                popup=f"<b>LIVE RIDER:</b> {route.courier_name}",
                icon=folium.Icon(color="blue", icon="motorcycle", prefix="fa"),
            ).add_to(m)
            
    st_folium(m, width=680, height=470)

with col_telemetry:
    st.markdown("### 📊 Freshness Telemetry")
    
    table_data = []
    for r in results.routes:
        for s in r.stops:
            for item_name, q in s.quality_indices.items():
                table_data.append({
                    "Rider": r.courier_name,
                    "Order": s.order_id,
                    "Item": item_name,
                    "ETA": f"{s.arrival_minute:.1f} min",
                    "Freshness": q,
                    "Status": "🟢 Safe" if s.is_safe else "🔴 Spoil Risk"
                })
                
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            column_config={
                "Freshness": st.column_config.ProgressColumn(
                    "Freshness Quality",
                    help="Calculated thermal decay remaining",
                    format="%.0f%%",
                    min_value=0.0,
                    max_value=1.0,
                ),
            },
            hide_index=True,
            use_container_width=True,
            height=470
        )
    else:
        st.info("No orders currently scheduled.")