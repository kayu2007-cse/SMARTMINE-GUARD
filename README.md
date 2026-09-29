# Mining Haul Truck Safety Dashboard — Setup & Run Guide

## Step 1: Install Flask (once)
Open a terminal in VS Code (Ctrl + `) and run:

```
pip install flask
```

## Step 2: Run the server
```
python app.py
```

## Step 3: Open your browser
Go to: http://127.0.0.1:5000

---

## File Structure
```
mining-dashboard/
├── app.py                    ← Flask backend (all 4 layers)
├── requirements.txt
└── templates/
    └── dashboard.html        ← Full dashboard UI
```

## Architecture (matching your diagram)

| Layer | Module | Code Location |
|-------|--------|---------------|
| Sensor Ingestion | GNSS, MMW Radar, IR/LWIR, C-V2X | `sensor_*()` functions in app.py |
| Analytics Core | Dust/Visibility, Obstacle Fusion | `analytics_*()` functions |
| Speed Calculator | ISO 21815 braking equation | `calc_safe_speed()` |
| Alert State Machine | 3-Tier GREEN/AMBER/RED | `alert_state_machine()` |
| Dashboard UI | Tri-Modal actuator display | dashboard.html |

## API
- `GET /`              → Dashboard page
- `GET /api/telemetry` → JSON data (all sensor + alert data, refreshes at 1 Hz)
