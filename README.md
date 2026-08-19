# 🧊 ZeroMelt Engine

> Dynamic Cold-Chain Logistics & Thermal VRPTW (Vehicle Routing Problem with Time Windows) Optimization Platform for Quick-Commerce Dark Stores.

---

## 📌 Features
- **Thermal Decay Kinetics:** First-order Arrhenius exponential shelf-life degradation modeling based on outdoor ambient temperatures.
- **Google OR-Tools VRPTW-PD Solver:** Multi-vehicle constraint satisfaction adhering to vehicle capacity, service handoff delays, and perishable quality thresholds.
- **OSRM Real Road Network Routing:** Street-level turn-by-turn geometry rendering.
- **FastAPI Dispatch Gateway:** RESTful API with automated OpenAPI / Swagger documentation.
- **Interactive Control Room:** Streamlit + Folium visualization suite for real-time fleet operations and telemetry monitoring.
- **Geospatial Rider Tracking:** Redis Geospatial index client with live GPS coordinate simulation.

---

## 🚀 Quickstart

### 1. Setup Environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt