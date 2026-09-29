"""
Mining Haul Truck Safety Monitoring Dashboard
Flask Backend - Real-time simulated sensor data feed
Architecture: Sensor Fusion → Analytics Core → Alert State Machine → Dashboard UI
"""

import math
import random
import time
from datetime import datetime
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ─────────────────────────────────────────────
#  Simulation State
# ─────────────────────────────────────────────
_sim_time = 0.0


def _tick():
    global _sim_time
    _sim_time = time.time()
    return _sim_time


# ─────────────────────────────────────────────
#  Layer 1 – Sensor Ingestion & Fusion
# ─────────────────────────────────────────────
def sensor_gnss():
    """GNSS (GPS + NavIC RTK) – Sub-decimeter Position & Pit Depth"""
    t = _sim_time
    return {
        "latitude":   -22.9068 + math.sin(t * 0.05) * 0.0002,
        "longitude":  -43.1729 + math.cos(t * 0.04) * 0.0002,
        "altitude_m":  210.0 + math.sin(t * 0.03) * 5.0,
        "pit_depth_m": 48.0 + math.sin(t * 0.02) * 3.0,
        "fix_quality": "RTK-Fixed",
        "accuracy_cm": round(2.4 + random.uniform(0, 0.8), 1),
    }


def sensor_mmw_radar():
    """MMW Radar 77 GHz FMCW – Azimuth 120°, Range 100 m"""
    objects = []
    base_count = 2 + int(math.sin(_sim_time * 0.1) + 1)
    for i in range(base_count):
        dist = round(random.uniform(8, 98), 1)
        az   = round(random.uniform(-60, 60), 1)
        objects.append({
            "id":         i + 1,
            "range_m":    dist,
            "azimuth_deg": az,
            "velocity_kmh": round(random.uniform(-5, 40), 1),
            "rcs_dbsm":   round(random.uniform(-10, 20), 1),
        })
    return {
        "azimuth_fov_deg": 120,
        "max_range_m":     100,
        "detected_objects": objects,
        "nearest_m":       min(o["range_m"] for o in objects) if objects else 100,
    }


def sensor_ir_lwir():
    """Dual-Spectrum IR/LWIR – 8–14 µm Microbolometer + CMOS"""
    t = _sim_time
    dust_cycle = (math.sin(t * 0.07) + 1) / 2        # 0..1
    visibility  = round(120.0 - dust_cycle * 80.0, 1)  # 40–120 m
    return {
        "dust_density_mg_m3": round(dust_cycle * 850.0, 1),
        "visibility_m":       visibility,
        "scene_temp_c":       round(28.0 + math.sin(t * 0.05) * 4.0, 1),
        "thermal_hot_spots":  int(dust_cycle * 3),
        "cmos_clarity_pct":   round((1 - dust_cycle) * 100.0, 1),
    }


def sensor_cv2x():
    """C-V2X / DSRC 5.9 GHz Mesh – Peer Vehicle Telemetry"""
    peers = []
    for i in range(3):
        peers.append({
            "vehicle_id":    f"HT-{700 + i}",
            "range_m":       round(random.uniform(20, 150), 1),
            "speed_kmh":     round(random.uniform(5, 35), 1),
            "heading_deg":   round(random.uniform(0, 360), 1),
            "alert_tier":    random.choice(["GREEN", "GREEN", "AMBER", "RED"]),
        })
    return {
        "mesh_frequency_ghz": 5.9,
        "protocol":           "C-V2X + DSRC",
        "active_peers":       peers,
        "latency_ms":         round(random.uniform(8, 22), 1),
    }


# ─────────────────────────────────────────────
#  Layer 2 – Real-Time Analytics & Safety Core
# ─────────────────────────────────────────────
def analytics_dust_visibility(ir_data):
    """Optical Dust Density & Visibility Model"""
    v   = ir_data["visibility_m"]
    d   = ir_data["dust_density_mg_m3"]
    # Koschmieder–adapted extinction for mine dust
    extinction = round(3.912 / max(v, 1.0), 4) if v > 0 else 9.99
    return {
        "visibility_m":           v,
        "dust_density_mg_m3":     d,
        "extinction_coeff_1_m":   extinction,
        "visibility_class":       (
            "CLEAR" if v > 100 else
            "MODERATE" if v > 60 else
            "POOR" if v > 30 else "HAZARDOUS"
        ),
    }


def analytics_obstacle_fusion(radar_data, cv2x_data):
    """Perimeter Obstacle Fusion Engine – merges Radar + V2X"""
    nearest_radar = radar_data["nearest_m"]
    peer_ranges   = [p["range_m"] for p in cv2x_data["active_peers"]]
    nearest_peer  = min(peer_ranges) if peer_ranges else 999
    nearest_any   = min(nearest_radar, nearest_peer)
    threat_class  = (
        "CRITICAL" if nearest_any < 15 else
        "WARNING"  if nearest_any < 35 else
        "CAUTION"  if nearest_any < 60 else
        "CLEAR"
    )
    return {
        "nearest_obstacle_m":   round(nearest_any, 1),
        "nearest_radar_m":      round(nearest_radar, 1),
        "nearest_peer_m":       round(nearest_peer, 1),
        "threat_classification": threat_class,
        "fused_object_count":   len(radar_data["detected_objects"]) + len(cv2x_data["active_peers"]),
    }


# ─────────────────────────────────────────────
#  Layer 3 – Dynamic Safe Speed Calculator
#            ISO 21815 Braking Equation
# ─────────────────────────────────────────────
def calc_safe_speed(visibility_m, nearest_obstacle_m, pit_depth_m):
    """
    ISO 21815 braking distance: d = v²/(2µg) + v·t_reaction
    Solve for v given stopping distance = min(visibility, obstacle) - safety_margin
    """
    MU            = 0.65        # haul-road tyre friction
    G             = 9.81
    T_REACTION    = 1.5         # driver reaction time (s)
    SAFETY_MARGIN = 10.0        # minimum buffer (m)
    GRADE_DEG     = max(0, (pit_depth_m - 200) * 0.05)  # ramp grade effect

    stopping_dist = max(min(visibility_m, nearest_obstacle_m) - SAFETY_MARGIN, 1.0)

    # quadratic: v² / (2·µ·g·cos θ) + v·t = stopping_dist
    cos_theta = math.cos(math.radians(GRADE_DEG))
    a         = 1.0 / (2.0 * MU * G * cos_theta)
    b         = T_REACTION
    c         = -stopping_dist
    discriminant = b**2 - 4 * a * c

    if discriminant < 0:
        v_safe_ms = 0.0
    else:
        v_safe_ms = (-b + math.sqrt(discriminant)) / (2 * a)

    v_safe_kmh = max(0.0, min(v_safe_ms * 3.6, 40.0))
    return {
        "safe_speed_kmh":     round(v_safe_kmh, 1),
        "stopping_distance_m": round(stopping_dist, 1),
        "grade_deg":           round(GRADE_DEG, 2),
        "friction_coeff":      MU,
        "reaction_time_s":     T_REACTION,
        "standard":            "ISO 21815",
    }


# ─────────────────────────────────────────────
#  Layer 4 – 3-Tier Alert State Machine
# ─────────────────────────────────────────────
def alert_state_machine(safe_speed, current_speed, obstacle, dust_vis):
    """
    TIER 1 – GREEN  : Nominal operations
    TIER 2 – AMBER  : Advisory – reduce speed
    TIER 3 – RED    : Emergency – AEB potential
    """
    speed_ratio = current_speed / max(safe_speed, 1.0)
    threat      = obstacle["threat_classification"]
    vis_class   = dust_vis["visibility_class"]

    if threat == "CRITICAL" or speed_ratio > 1.30 or vis_class == "HAZARDOUS":
        tier = "RED"
        light_mode   = "Red 8 Hz Strobe"
        buzzer_mode  = "105 dB Piezo Klaxon"
        aeb_armed    = True
        message      = "EMERGENCY – AEB ARMED – REDUCE SPEED IMMEDIATELY"
    elif threat == "WARNING" or speed_ratio > 1.10 or vis_class == "POOR":
        tier = "AMBER"
        light_mode   = "Amber Pulse"
        buzzer_mode  = "78 dB Chime"
        aeb_armed    = False
        message      = "CAUTION – Speed Advisory Active – Slow Down"
    else:
        tier = "GREEN"
        light_mode   = "Solid Green"
        buzzer_mode  = "Standby"
        aeb_armed    = False
        message      = "NOMINAL – All Systems Clear"

    return {
        "tier":        tier,
        "light_mode":  light_mode,
        "buzzer_mode": buzzer_mode,
        "aeb_armed":   aeb_armed,
        "message":     message,
        "speed_ratio": round(speed_ratio, 2),
    }


# ─────────────────────────────────────────────
#  API Endpoints
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/telemetry")
def telemetry():
    _tick()

    # Simulate current truck speed
    current_speed_kmh = round(
        20.0 + math.sin(_sim_time * 0.08) * 12.0 + random.uniform(-1, 1), 1
    )

    # Layer 1 – Sensors
    gnss   = sensor_gnss()
    radar  = sensor_mmw_radar()
    ir     = sensor_ir_lwir()
    cv2x   = sensor_cv2x()

    # Layer 2 – Analytics
    dust_vis = analytics_dust_visibility(ir)
    obstacle = analytics_obstacle_fusion(radar, cv2x)

    # Layer 3 – Speed Calculator
    speed_calc = calc_safe_speed(
        dust_vis["visibility_m"],
        obstacle["nearest_obstacle_m"],
        gnss["pit_depth_m"],
    )

    # Layer 4 – Alert
    alert = alert_state_machine(
        speed_calc["safe_speed_kmh"],
        current_speed_kmh,
        obstacle,
        dust_vis,
    )

    return jsonify({
        "timestamp":        datetime.utcnow().isoformat() + "Z",
        "current_speed_kmh": current_speed_kmh,
        "sensors": {
            "gnss":  gnss,
            "radar": radar,
            "ir":    ir,
            "cv2x":  cv2x,
        },
        "analytics": {
            "dust_visibility": dust_vis,
            "obstacle_fusion": obstacle,
        },
        "speed_calculator": speed_calc,
        "alert":            alert,
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  Mining Haul Truck Safety Dashboard")
    print("  Server: http://0.0.0.0:5000")
    print("  Network access: http://<your-pc-ip>:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)


