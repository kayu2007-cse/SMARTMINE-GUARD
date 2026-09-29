# 🚧 SMARTMINE GUARD

### Intelligent Safety Assistance System for Mining Haul Trucks

SMARTMINE GUARD is a multi-sensor mining safety assistance system designed to improve the situational awareness of haul-truck operators in challenging mining environments such as dust, fog, low visibility, blind spots, and congested haul roads.

The prototype combines GNSS/NavIC, 77 GHz mmWave radar, IR/LWIR thermal sensing, and V2X telemetry with sensor-fusion analytics, dynamic safe-speed calculation, and a three-level safety alert system.

---

## 📌 Problem Statement

Mining haul trucks operate in large, complex environments where dust, fog, poor visibility, blind spots, and nearby vehicles can increase the risk of collisions.

Conventional vehicle safety systems may have limitations in such environments because a single sensing technology may not provide reliable situational awareness under all conditions.

SMARTMINE GUARD addresses this challenge through a multi-sensor safety architecture that combines different sources of vehicle and environmental information.

---

## 💡 Proposed Solution

SMARTMINE GUARD continuously processes simulated sensor data and performs real-time safety analysis.

The system:

- Monitors vehicle position and elevation using GNSS/NavIC data
- Detects nearby obstacles using 77 GHz mmWave radar
- Estimates dust and visibility conditions using IR/LWIR data
- Receives nearby vehicle telemetry through V2X communication
- Fuses sensor information for obstacle and threat assessment
- Calculates a dynamic recommended safe speed
- Generates GREEN, AMBER, and RED safety states
- Provides actuator/status information through a web dashboard

> **Prototype Note:** The current software prototype uses simulated sensor data. Physical sensor and vehicle-controller integration can be added during hardware implementation.

---

# 🏗️ System Architecture

```text
                  ┌─────────────────────────┐
                  │      SENSOR LAYER       │
                  ├─────────────────────────┤
                  │ GNSS / NavIC            │
                  │ 77 GHz mmWave Radar     │
                  │ IR / LWIR               │
                  │ C-V2X / DSRC            │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │    SENSOR FUSION         │
                  │                         │
                  │ Radar + V2X + GNSS +    │
                  │ Environmental Data      │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │     ANALYTICS CORE      │
                  ├─────────────────────────┤
                  │ Dust / Visibility       │
                  │ Obstacle Detection      │
                  │ Threat Assessment       │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   SAFE-SPEED ENGINE     │
                  │                         │
                  │ Braking Distance +      │
                  │ Reaction Time + Safety  │
                  │ Margin                   │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │  ALERT STATE MACHINE     │
                  ├─────────────────────────┤
                  │ 🟢 GREEN                │
                  │ 🟠 AMBER                │
                  │ 🔴 RED                  │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   WEB SAFETY DASHBOARD  │
                  │                         │
                  │ Telemetry • Alerts      │
                  │ Sensor Status • Speed   │
                  └─────────────────────────┘
