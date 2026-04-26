from flask import Blueprint, render_template, current_app, abort

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
        },
        {
            'type': 'network',
            'title': 'Network Topology',
            'description': '노드와 링크로 구성된 가상 네트워크 토폴로지를 시뮬레이션합니다. 데이터 흐름을 시각적으로 확인하세요.',
            'thumbnail': '/static/images/site/icon/network.png'
        },
        {
            'type': 'gravity',
            'title': 'Gravity Field',
            'description': '질량을 가진 물체들 사이의 중력 상호작용을 시뮬레이션합니다. 궤도와 충돌을 관찰해보세요.',
            'thumbnail': '/static/images/site/icon/gps.png'
        }
    ]
    return render_template('simulation/index.html', simulations=simulations)

@simulation_bp.route('/<simulation_type>')
def dynamic_simulation(simulation_type):
    """Render a specific simulation page."""
    valid_sims = ['particles', 'network', 'gravity']
    if simulation_type not in valid_sims:
        abort(404)
        
    return render_template(f'simulation/{simulation_type}.html', simulation_type=simulation_type)
