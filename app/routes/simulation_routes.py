from flask import Blueprint, render_template, abort

simulation_bp = Blueprint('simulation', __name__, url_prefix='/simulation')

@simulation_bp.route('/')
def index():
    """Render the simulation hub page."""
    simulations = [
        {
            'type': 'particles',
            'title': 'Cyberpixel Particles',
            'description': '사이버픽셀 테마의 인터랙티브 입자 시스템입니다. 마우스 움직임에 반응하는 네온 입자들을 체험해보세요.',
            'thumbnail': '/static/images/site/icon/simulation.png'
        }
    ]
    return render_template('simulation/index.html', simulations=simulations)

@simulation_bp.route('/<simulation_type>')
def dynamic_simulation(simulation_type):
    """Render a specific simulation page."""
    valid_sims = ['particles']
    if simulation_type not in valid_sims:
        abort(404)
        
    return render_template(f'simulation/{simulation_type}.html', simulation_type=simulation_type)
