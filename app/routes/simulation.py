# app/routes/simulation.py
from flask import Blueprint, render_template, current_app


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

# 다이나믹 라우트는 마지막에 정의하고 예외 처리 개선
@simulation_bp.route('/<string:type>')
def simulation_type(type):
    # 이미 정의된 라우트와 충돌하지 않도록 확인
    if type in ['particles', 'pendulum']:
        return simulation_bp.view_functions[f'simulation.{type}_simulation']()
    
    # 디버깅 로그 추가
    current_app.logger.debug(f"Simulation type requested: {type}")
    try:
        return render_template(f'simulation/{type}.html')
    except Exception as e:
        current_app.logger.error(f"Error loading simulation template: {str(e)}")
        return f"Error: Cannot load simulation type '{type}'. Details: {str(e)}", 404