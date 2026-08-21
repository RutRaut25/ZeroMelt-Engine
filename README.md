## 🏗️ System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph INGESTION["  📥 INGESTION & SENSING LAYER  "]
        Orders["📦 <b>Customer Order Batch</b><br><small>SKUs, GPS Coordinates, Payloads</small>"]
        Weather["🌡️ <b>Ambient Weather Sensor</b><br><small>Real-time Zone Temperature (°C)</small>"]
    end

    subgraph ENGINE["  ⚙️ OPTIMIZATION & PHYSICS ENGINE  "]
        Decay["🧪 <b>Arrhenius Thermal Kinetics</b><br><code>Q(t) = Q₀ · exp(-k · t)</code><br><small>Dynamic Spoilage Time Windows</small>"]
        Graph["🗺️ <b>OSRM Road Network Matrix</b><br><small>Street Geometry & Travel Durations</small>"]
        Solver["🚀 <b>Google OR-Tools VRPTW Solver</b><br><small>Multi-Vehicle Guided Local Search</small>"]
    end

    subgraph OUTPUT["  🛰️ REAL-TIME DISPATCH & MONITORING  "]
        API["⚡ <b>FastAPI Gateway</b><br><small>Dispatch Endpoints & OpenAPI Docs</small>"]
        Redis[("💾 <b>Redis Geo Cache</b><br><small>Live Courier Coordinates</small>")]
        Dashboard["📊 <b>Streamlit Control Room</b><br><small>Interactive Maps & Freshness Telemetry</small>"]
    end

    Orders --> Decay
    Weather --> Decay
    Decay --> Solver
    Graph --> Solver
    Solver ==> API
    Solver ==> Dashboard
    API -.-> Redis
    Redis -.-> Dashboard

    style INGESTION fill:#0f172a,stroke:#38bdf8,stroke-width:1.5px,stroke-dasharray: 4 4,color:#38bdf8
    style ENGINE fill:#090d16,stroke:#818cf8,stroke-width:2px,color:#818cf8
    style OUTPUT fill:#064e3b,stroke:#34d399,stroke-width:1.5px,stroke-dasharray: 4 4,color:#34d399

    style Orders fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc
    style Weather fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc
    style Decay fill:#312e81,stroke:#a5b4fc,stroke-width:2px,color:#ffffff
    style Graph fill:#312e81,stroke:#a5b4fc,stroke-width:2px,color:#ffffff
    style Solver fill:#4c1d95,stroke:#c084fc,stroke-width:2.5px,color:#ffffff
    style API fill:#022c22,stroke:#34d399,stroke-width:2px,color:#f8fafc
    style Redis fill:#022c22,stroke:#34d399,stroke-width:2px,color:#f8fafc
    style Dashboard fill:#022c22,stroke:#34d399,stroke-width:2px,color:#f8fafc

    click Orders href "[https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/schemas.py](https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/schemas.py)" "View Data Contracts" _blank
    click Decay href "[https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/decay.py](https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/decay.py)" "View Thermal Physics Code" _blank
    click Graph href "[https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/graph.py](https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/graph.py)" "View Road Network & OSRM Routing" _blank
    click Solver href "[https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/solver.py](https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/solver.py)" "View OR-Tools Solver Engine" _blank
    click API href "[https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/main.py](https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/main.py)" "View FastAPI Gateway" _blank
    click Dashboard href "[https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/dashboard/app.py](https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/dashboard/app.py)" "View Streamlit Dashboard" _blank
    click Redis href "[https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/redis_client.py](https://github.com/RutRaut25/ZeroMelt-Engine/blob/main/app/redis_client.py)" "View Geospatial Redis Cache" _blank
```