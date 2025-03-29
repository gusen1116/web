from flask import Blueprint, render_template, jsonify, request
import os

simulation_bp = Blueprint('simulation', __name__, url_prefix='/simulation')

@simulation_bp.route('/')
def index():
    """Simulation index page"""
    return render_template('simulation/index.html')

@simulation_bp.route('/a320')
def a320_simulation():
    """A320 wing system simulation page"""
    # Pass any initial parameters if needed
    return render_template('simulation/a320.html', 
                        title="Airbus A320 Wing System Simulation",
                        description="Interactive simulation of the Airbus A320 wing and high-lift devices")

@simulation_bp.route('/a320/info')
def a320_info():
    """Return information about the A320 wing system"""
    info = {
        "name": "Airbus A320 Wing System",
        "description": "Realistic simulation of the A320 wing with high-lift devices including slats, flaps, and spoilers.",
        "specifications": {
            "wing_span": "35.8 meters (with winglets)",
            "wing_area": "122.6 square meters",
            "aspect_ratio": "9.39",
            "sweep_angle": "25 degrees (at quarter-chord)",
            "airfoil_type": "Supercritical airfoil with 11.5% thickness-to-chord ratio",
            "high_lift_devices": [
                "Leading edge slats with 5 positions (UP, MID, 1, 2, 3)",
                "Trailing edge flaps with 5 positions (UP, 1, 2, 3, FULL)",
                "Spoilers for lift dumping and roll control"
            ]
        },
        "capabilities": [
            "Realistic aerodynamic simulation based on actual A320 data",
            "Interactive control of flight parameters",
            "Visualization of airfoil shape, pressure distribution, and flow field",
            "Real-time calculation of lift, drag, and performance metrics"
        ]
    }
    return jsonify(info)

@simulation_bp.route('/particles')
def particle_simulation():
    """Simple particle physics simulation page"""
    return render_template('simulation/particles.html')

@simulation_bp.route('/pendulum')
def pendulum_simulation():
    """Pendulum simulation page"""
    return render_template('simulation/pendulum.html')