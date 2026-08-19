<div align="center">

# 🧊 ZeroMelt Engine
### Dynamic Cold-Chain Logistics & Thermal VRPTW Optimization Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![OR-Tools](https://img.shields.io/badge/Google_OR--Tools-Optimization-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/optimization)

*An intelligent quick-commerce dispatch and vehicle routing system that dynamically prevents perishable degradation using real-time thermal kinetics, Google OR-Tools constraint satisfaction, and street-level road network routing.*

</div>

---

## 📌 Problem Overview

In quick-commerce (10–20 minute delivery windows), high ambient temperatures cause perishable items (ice cream, frozen poultry, dairy, produce) to spoil or melt before reaching customers. Standard routing algorithms optimize strictly for distance or generic delivery deadlines, ignoring thermal degradation.

**ZeroMelt Engine** bridges thermodynamics and combinatorial optimization:
1. Translates ambient weather temperatures and item shelf-life kinetics into hard, dynamic delivery time windows.
2. Formulates a **Vehicle Routing Problem with Time Windows and Perishable Decay (VRPTW-PD)**.
3. Computes multi-courier routes ensuring $0\%$ cold-chain spoilage.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Customer Order Batch                     │
│    (Items, Categories, Weights, Geographic Coordinates)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Thermal Decay Kinetic Engine (decay.py)         │
│          Q(t) = Q₀ · exp( -k · (T_amb / T_ref) · t )        │
│          Calculates dynamic safe arrival deadlines          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Spatial Graph & OSRM Engine (graph.py)            │
│         Distance Matrix + Street-level Turn Geometry        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│        Google OR-Tools VRPTW Solver (solver.py)             │
│    - Vehicle Capacity Limits    - Service Handoff Delays    │
│    - Cold-Chain Time Windows    - Guided Local Search       │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│    FastAPI REST Gateway     │ │  Streamlit Operations Room  │
│       (app/main.py)         │ │    (dashboard/app.py)       │
│  Live Dispatch JSON API     │ │  Interactive Map & Telemetry│
└─────────────────────────────┘ └─────────────────────────────┘