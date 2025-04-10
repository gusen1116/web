from flask import Blueprint, render_template

simulation_bp = Blueprint('simulation', __name__, url_prefix='/simulation')

@simulation_bp.route('/')
def index():
    """Simulation index page"""
    return render_template('simulation/index.html')


@simulation_bp.route('/particles')
def particle_simulation():
    """Simple particle physics simulation page"""
    return render_template('simulation/particles.html')

@simulation_bp.route('/pendulum')
def pendulum_simulation():
    """Pendulum simulation page"""
    return render_template('simulation/pendulum.html')