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

spatial_store = FleetSpatialStore()

st.set_page_config(layout="wide", page_title="ZeroMelt Control Center", page_icon="🧊")

st.title("🧊 ZeroMelt Engine: Fleet Dispatch & Cold-Chain Control")
st.markdown("Dynamic vehicle routing with thermal decay kinetics & hard time windows.")

# --- Sidebar Configuration ---
st.sidebar.header("🕹️ Fleet & Weather Controls")
ambient_temp = st.sidebar.slider("Ambient Temperature (°C)", min_value=15.0, max_value=45.0, value=35.0, step=1.0)
num_couriers = st.sidebar.slider("Active Couriers", min_value=1, max_value=4, value=2)
payload_cap = st.sidebar.number_input("Courier Payload Limit (kg)", value=10.0, step=1.0)

# Central Hub Depot
HUB = DarkStoreHub(
    hub_id="HUB_01",
    name="Central Hub",
    latitude=18.5074,
    longitude=73.8077
)

# Simulated Batch Orders
MOCK_ORDERS = [
    Order(
        order_id="ORD-101",
        latitude=18.5145, longitude=73.8180,
        earliest_minute=0, latest_minute=20,
        items=[OrderItem(name="Belgian Chocolate Tub", category=ItemCategory.FROZEN, weight_kg=0.8)]
    ),
    Order(
        order_id="ORD-102",
        latitude=18.5250, longitude=73.8300,
        earliest_minute=0, latest_minute=30,
        items=[OrderItem(name="Organic Whole Milk 1L", category=ItemCategory.CHILLED, weight_kg=1.0)]
    ),
    Order(
        order_id="ORD-103",
        latitude=18.5020, longitude=73.8250,
        earliest_minute=0, latest_minute=25,
        items=[OrderItem(name="Fresh Farm Poultry", category=ItemCategory.CHILLED, weight_kg=1.2)]
    ),
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
    ),
    Order(
        order_id="ORD-106",
        latitude=18.5190, longitude=73.7910,
        earliest_minute=0, latest_minute=18,
        items=[OrderItem(name="Vanilla Bean Gelato", category=ItemCategory.FROZEN, weight_kg=0.7)]
    )
]

COURIERS = [
    Courier(courier_id=f"RIDER-0{i+1}", name=f"Courier #{i+1}", max_payload_kg=payload_cap)
    for i in range(num_couriers)
]

# --- Execute Solver ---
solver = ColdChainVRPTSolver(hub=HUB, orders=MOCK_ORDERS, couriers=COURIERS, ambient_temp_c=ambient_temp)
results = solver.solve()

# --- Metric KPI Cards ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Solver Status", results.status)
kpi2.metric("Fleet Total Distance", f"{results.total_distance_km} km")
kpi3.metric(
    "Fleet Spoilage Rate",
    f"{results.fleet_spoilage_rate_pct}%",
    delta="0.0% (Zero Melt)" if results.fleet_spoilage_rate_pct == 0 else f"+{results.fleet_spoilage_rate_pct}% SPOILAGE",
    delta_color="inverse"
)
kpi4.metric("Simulated Temp", f"{ambient_temp}°C")

st.divider()

# --- Viewport: Map & Telemetry ---
map_col, table_col = st.columns([3, 2])

with map_col:
    st.subheader("🗺️ Live Street-Routed Paths (OSRM)")
    m = folium.Map(location=[HUB.latitude, HUB.longitude], zoom_start=13, tiles="CartoDB positron")
    
    # Hub Marker
    folium.Marker(
        [HUB.latitude, HUB.longitude],
        popup=f"<b>DarkStore Depot:</b> {HUB.name}",
        icon=folium.Icon(color="black", icon="home", prefix="fa"),
    ).add_to(m)
    
    ROUTE_COLORS = ["blue", "green", "purple", "orange", "darkred"]
    
    for c_idx, route in enumerate(results.routes):
        color = ROUTE_COLORS[c_idx % len(ROUTE_COLORS)]
        current_loc = (HUB.latitude, HUB.longitude)
        
        for stop in route.stops:
            next_loc = (stop.latitude, stop.longitude)
            segment_geometry = get_osrm_route_geometry(current_loc, next_loc)
            folium.PolyLine(segment_geometry, color=color, weight=4, opacity=0.85, tooltip=f"{route.courier_name} Path").add_to(m)
            current_loc = next_loc
            
            stop_icon_color = "green" if stop.is_safe else "red"
            q_summary = "<br>".join([f"{k}: {int(v*100)}%" for k, v in stop.quality_indices.items()])
            popup_html = f"""
            <b>Order:</b> {stop.order_id}<br>
            <b>Courier:</b> {route.courier_name}<br>
            <b>ETA:</b> {stop.arrival_minute:.1f} min<br>
            <b>Freshness:</b><br>{q_summary}
            """
            folium.Marker(
                [stop.latitude, stop.longitude],
                popup=popup_html,
                icon=folium.Icon(color=stop_icon_color, icon="shopping-cart", prefix="fa"),
            ).add_to(m)
            
        # Return path
        return_geometry = get_osrm_route_geometry(current_loc, (HUB.latitude, HUB.longitude))
        folium.PolyLine(return_geometry, color=color, weight=3, opacity=0.6, dash_array="5, 10").add_to(m)

        # Check for live GPS coordinates from Redis store
        live_gps = spatial_store.get_rider_position(route.courier_id)
        if live_gps:
            folium.Marker(
                [live_gps[0], live_gps[1]],
                popup=f"<b>LIVE GPS:</b> {route.courier_name}",
                icon=folium.Icon(color="darkblue", icon="motorcycle", prefix="fa"),
            ).add_to(m)

    st_folium(m, width=720, height=480)

with table_col:
    st.subheader("📊 Cold-Chain Telemetry")
    table_rows = []
    for r in results.routes:
        for s in r.stops:
            for item_name, q in s.quality_indices.items():
                table_rows.append({
                    "Rider": r.courier_name,
                    "Order": s.order_id,
                    "Item": item_name,
                    "ETA (min)": s.arrival_minute,
                    "Freshness": f"{int(q*100)}%",
                    "Status": "Safe 🟢" if s.is_safe else "SPOILED 🔴"
                })
    if table_rows:
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, height=440)