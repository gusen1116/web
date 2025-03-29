"""
Extended Flask routes for A320 visualization
Adds endpoints for advanced matplotlib visualizations
"""

from flask import Blueprint, render_template, jsonify, request, Response
import io
import base64
from app.services.a320_aerodynamics import A320WingAerodynamics
from app.services.wing_visualizer import WingVisualizer

# Create global instances for visualization
simulation_instance = A320WingAerodynamics()
visualizer = WingVisualizer(simulation_instance)

# Create blueprint
visualization_bp = Blueprint('visualization', __name__, url_prefix='/visualization')

@visualization_bp.route('/a320/<plot_type>')
def get_visualization(plot_type):
    """
    Generate and return a visualization as an image
    
    Args:
        plot_type: Type of plot to generate ('pressure', 'airfoil', 'polar')
    
    Returns:
        HTTP response with the image data
    """
    # Optional parameters
    aoa = request.args.get('aoa', type=float)
    mach = request.args.get('mach', type=float)
    flap_setting = request.args.get('flap', type=str)
    slat_setting = request.args.get('slat', type=str)
    
    # Update simulation parameters if provided
    if aoa is not None:
        simulation_instance.state["angle_of_attack"] = aoa
    
    if mach is not None:
        # Convert Mach to airspeed
        simulation_instance.state["airspeed"] = mach * 340.3
    
    if flap_setting is not None:
        simulation_instance.update_settings({"flap_setting": flap_setting})
    
    if slat_setting is not None:
        simulation_instance.update_settings({"slat_setting": slat_setting})
    
    # Recompute simulation with updated parameters
    simulation_instance._compute_simulation()
    
    # Generate the visualization
    image_data = visualizer.generate_visualization_endpoint(plot_type)
    
    if image_data:
        # Parse the data URL
        header, encoded = image_data.split(",", 1)
        data = base64.b64decode(encoded)
        
        # Return as an image
        return Response(data, mimetype='image/png')
    else:
        return jsonify({
            "error": "Invalid plot type",
            "valid_types": ["pressure", "airfoil", "polar"]
        }), 400

@visualization_bp.route('/a320/data')
def get_visualization_data():
    """
    Return JSON data with all visualization URLs for embedding
    """
    # Base URL for the current request
    base_url = request.url_root.rstrip('/')
    
    # Current simulation state
    aoa = simulation_instance.state["angle_of_attack"]
    mach = simulation_instance.results["mach_number"]
    flap = simulation_instance.state["flap_setting"]
    slat = simulation_instance.state["slat_setting"]
    
    # Generate URLs with current parameters
    pressure_url = f"{base_url}/visualization/a320/pressure?aoa={aoa}&mach={mach}&flap={flap}&slat={slat}"
    airfoil_url = f"{base_url}/visualization/a320/airfoil?aoa={aoa}&flap={flap}&slat={slat}"
    polar_url = f"{base_url}/visualization/a320/polar?mach={mach}&flap={flap}&slat={slat}"
    
    # Return JSON with URLs
    return jsonify({
        "pressure_plot": pressure_url,
        "airfoil_plot": airfoil_url,
        "polar_plot": polar_url,
        "current_state": {
            "angle_of_attack": aoa,
            "mach_number": mach,
            "flap_setting": flap,
            "slat_setting": slat,
            "lift_coefficient": simulation_instance.results["lift_coefficient"],
            "drag_coefficient": simulation_instance.results["drag_coefficient"]
        }
    })

@visualization_bp.route('/a320/dashboard')
def visualization_dashboard():
    """Render a dashboard with all visualizations"""
    return render_template('simulation/a320_dashboard.html',
                        title="A320 Wing System Analysis Dashboard",
                        description="Comprehensive analysis of A320 aerodynamics with high-lift devices")

def register_visualization_routes(app):
    """Register visualization routes with the Flask app"""
    app.register_blueprint(visualization_bp)