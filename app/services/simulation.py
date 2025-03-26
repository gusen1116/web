# app/routes/simulation.py
from flask import Blueprint, render_template

simulation_bp = Blueprint('simulation', __name__, url_prefix='/simulation')

@simulation_bp.route('/')
def index():
    return render_template('simulation/index.html')

@simulation_bp.route('/<string:type>')
def simulation_type(type):
    # 시뮬레이션 타입에 따라 다른 템플릿 렌더링
    if type == 'particles':
        return render_template('simulation/particles.html')
    elif type == 'airfoil':
        return render_template('simulation/airfoil.html')
    elif type == 'pendulum':
        return render_template('simulation/pendulum.html')
    else:
        # 알 수 없는 시뮬레이션 타입인 경우 메인 페이지로 리디렉션
        return render_template('simulation/index.html')