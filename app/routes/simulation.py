# app/routes/simulation.py
from flask import Blueprint, render_template

simulation_bp = Blueprint('simulation', __name__)

@simulation_bp.route('/simulation')
def index():
    return render_template('simulation/index.html')

@simulation_bp.route('/simulation/<string:type>')
def simulation_type(type):
    return render_template(f'simulation/{type}.html')