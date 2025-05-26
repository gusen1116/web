# app/routes/simulation.py
from flask import Blueprint, render_template, current_app, abort, request
from typing import Dict, List, Optional
import re

# 블루프린트 생성
simulation_bp = Blueprint('simulation', __name__, url_prefix='/simulation')

# 허용된 시뮬레이션 타입 (보안 및 유지보수성)
ALLOWED_SIMULATION_TYPES = {
    'particles': {
        'template': 'simulation/particles.html',
        'title': '입자 물리 시뮬레이션',
        'description': '물리 법칙에 따라 상호작용하는 입자들의 움직임을 관찰할 수 있습니다.'
    },
    'pendulum': {
        'template': 'simulation/pendulum.html', 
        'title': '진자 시뮬레이션',
        'description': '중력과 마찰의 영향을 받는 진자의 움직임을 시뮬레이션합니다.'
    }
}

# 안전한 시뮬레이션 타입 패턴
SAFE_SIMULATION_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]{1,50}$')


@simulation_bp.route('/')
def index():
    """
    시뮬레이션 메인 페이지 - 개선된 버전
    
    주요 개선사항:
    - 시뮬레이션 목록 자동 생성
    - 메타데이터 기반 정보 제공
    - 오류 처리 강화
    """
    try:
        # 사용 가능한 시뮬레이션 목록 생성
        simulations = []
        for sim_type, sim_info in ALLOWED_SIMULATION_TYPES.items():
            simulations.append({
                'type': sim_type,
                'title': sim_info['title'],
                'description': sim_info['description'],
                'url': f'/simulation/{sim_type}',
                'thumbnail': f'/static/img/simulation-{sim_type}.png'  # 썸네일 이미지 (옵션)
            })
        
        return render_template(
            'simulation/index.html',
            simulations=simulations,
            total_simulations=len(simulations)
        )
        
    except Exception as e:
        current_app.logger.error(f'시뮬레이션 인덱스 페이지 오류: {e}')
        return render_template('simulation/index.html', simulations=[], error=True)


@simulation_bp.route('/particles')
def particle_simulation():
    """입자 물리 시뮬레이션 페이지"""
    try:
        return render_template(
            'simulation/particles.html',
            page_title='입자 물리 시뮬레이션',
            simulation_type='particles'
        )
    except Exception as e:
        current_app.logger.error(f'입자 시뮬레이션 페이지 오류: {e}')
        abort(500)


@simulation_bp.route('/pendulum') 
def pendulum_simulation():
    """진자 시뮬레이션 페이지"""
    try:
        return render_template(
            'simulation/pendulum.html',
            page_title='진자 시뮬레이션',
            simulation_type='pendulum'
        )
    except Exception as e:
        current_app.logger.error(f'진자 시뮬레이션 페이지 오류: {e}')
        abort(500)


@simulation_bp.route('/<string:simulation_type>')
def dynamic_simulation(simulation_type: str):
    """
    동적 시뮬레이션 라우트 - 보안 강화
    
    Args:
        simulation_type: 시뮬레이션 타입
        
    Returns:
        Response: 해당 시뮬레이션 페이지 또는 404
    """
    try:
        # 입력 검증
        if not simulation_type or not isinstance(simulation_type, str):
            abort(400)
        
        # 보안 패턴 검증
        if not SAFE_SIMULATION_PATTERN.match(simulation_type):
            current_app.logger.warning(f'잘못된 시뮬레이션 타입 접근: {simulation_type}')
            abort(400)
        
        # 허용된 시뮬레이션 타입인지 확인
        if simulation_type not in ALLOWED_SIMULATION_TYPES:
            current_app.logger.info(f'존재하지 않는 시뮬레이션 타입: {simulation_type}')
            abort(404)
        
        # 정적 라우트와 중복 방지
        static_routes = ['particles', 'pendulum']
        if simulation_type in static_routes:
            # 해당 정적 라우트로 리다이렉트
            from flask import redirect, url_for
            return redirect(url_for(f'simulation.{simulation_type}_simulation'))
        
        # 시뮬레이션 정보 가져오기
        sim_info = ALLOWED_SIMULATION_TYPES[simulation_type]
        
        # 템플릿 렌더링
        return render_template(
            sim_info['template'],
            page_title=sim_info['title'],
            simulation_type=simulation_type,
            description=sim_info['description']
        )
        
    except Exception as e:
        current_app.logger.error(f'동적 시뮬레이션 라우트 오류 {simulation_type}: {e}')
        abort(500)


@simulation_bp.route('/api/<simulation_type>/config')
def api_simulation_config(simulation_type: str):
    """
    시뮬레이션 설정 API - 클라이언트용 설정 정보 제공
    
    Args:
        simulation_type: 시뮬레이션 타입
        
    Returns:
        JSON: 시뮬레이션 설정 정보
    """
    try:
        # 입력 검증
        if not SAFE_SIMULATION_PATTERN.match(simulation_type):
            return {'error': '잘못된 시뮬레이션 타입'}, 400
        
        if simulation_type not in ALLOWED_SIMULATION_TYPES:
            return {'error': '지원하지 않는 시뮬레이션'}, 404
        
        # 시뮬레이션별 기본 설정
        configs = {
            'particles': {
                'default_particle_count': 30,
                'max_particle_count': 100,
                'default_gravity': 9.8,
                'max_gravity': 20.0,
                'default_friction': 0.01,
                'max_friction': 0.1,
                'default_elasticity': 0.8,
                'canvas_size': {'width': 800, 'height': 400},
                'physics': {
                    'collision_detection': True,
                    'boundary_collision': True,
                    'particle_interaction': True
                }
            },
            'pendulum': {
                'default_length': 200,
                'max_length': 400,
                'default_mass': 1.0,
                'max_mass': 5.0,
                'default_gravity': 9.8,
                'default_damping': 0.01,
                'canvas_size': {'width': 600, 'height': 400},
                'physics': {
                    'gravity_enabled': True,
                    'damping_enabled': True,
                    'trace_enabled': False
                }
            }
        }
        
        config = configs.get(simulation_type, {})
        
        return {
            'type': simulation_type,
            'title': ALLOWED_SIMULATION_TYPES[simulation_type]['title'],
            'config': config,
            'version': '2.0'
        }
        
    except Exception as e:
        current_app.logger.error(f'시뮬레이션 설정 API 오류: {e}')
        return {'error': '서버 오류'}, 500


@simulation_bp.route('/api/list')
def api_simulation_list():
    """
    사용 가능한 시뮬레이션 목록 API
    
    Returns:
        JSON: 시뮬레이션 목록
    """
    try:
        simulations = []
        
        for sim_type, sim_info in ALLOWED_SIMULATION_TYPES.items():
            simulations.append({
                'type': sim_type,
                'title': sim_info['title'],
                'description': sim_info['description'],
                'url': f'/simulation/{sim_type}',
                'api_config_url': f'/simulation/api/{sim_type}/config'
            })
        
        return {
            'simulations': simulations,
            'total': len(simulations),
            'version': '2.0'
        }
        
    except Exception as e:
        current_app.logger.error(f'시뮬레이션 목록 API 오류: {e}')
        return {'error': '서버 오류'}, 500


# ===== 유틸리티 함수들 =====

def _validate_simulation_params(params: Dict) -> Dict:
    """
    시뮬레이션 파라미터 검증 및 정규화
    
    Args:
        params: 입력 파라미터
        
    Returns:
        Dict: 검증된 파라미터
    """
    validated = {}
    
    # 숫자 파라미터 검증
    numeric_params = {
        'gravity': {'min': 0, 'max': 50, 'default': 9.8},
        'friction': {'min': 0, 'max': 1, 'default': 0.01},
        'elasticity': {'min': 0, 'max': 1, 'default': 0.8},
        'particle_count': {'min': 1, 'max': 200, 'default': 30}
    }
    
    for param, config in numeric_params.items():
        if param in params:
            try:
                value = float(params[param])
                validated[param] = max(config['min'], min(config['max'], value))
            except (ValueError, TypeError):
                validated[param] = config['default']
        else:
            validated[param] = config['default']
    
    # 불린 파라미터 검증
    boolean_params = {
        'collision_enabled': True,
        'gravity_enabled': True,
        'trace_enabled': False
    }
    
    for param, default in boolean_params.items():
        if param in params:
            validated[param] = bool(params[param])
        else:
            validated[param] = default
    
    return validated


# ===== 에러 핸들러 =====

@simulation_bp.errorhandler(400)
def bad_request_handler(error):
    """400 에러 핸들러"""
    return render_template('400.html', error=error), 400


@simulation_bp.errorhandler(404) 
def not_found_handler(error):
    """404 에러 핸들러 - 시뮬레이션 전용"""
    current_app.logger.info(f'시뮬레이션 404: {request.url}')
    
    # 사용 가능한 시뮬레이션 목록과 함께 404 페이지 표시
    try:
        available_simulations = list(ALLOWED_SIMULATION_TYPES.keys())
        return render_template(
            '404.html', 
            error=error,
            available_simulations=available_simulations,
            simulation_context=True
        ), 404
    except Exception:
        return render_template('404.html', error=error), 404


@simulation_bp.errorhandler(500)
def internal_error_handler(error):
    """500 에러 핸들러"""
    return render_template('500.html', error=error), 500


# ===== 라우트 등록 검증 (개발 도구) =====

@simulation_bp.before_app_first_request
def verify_simulation_templates():
    """
    애플리케이션 시작 시 시뮬레이션 템플릿 존재 여부 확인
    누락된 템플릿이 있으면 경고 로그 출력
    """
    try:
        from pathlib import Path
        template_dir = Path(current_app.template_folder)
        
        missing_templates = []
        
        for sim_type, sim_info in ALLOWED_SIMULATION_TYPES.items():
            template_path = template_dir / sim_info['template']
            if not template_path.exists():
                missing_templates.append(sim_info['template'])
        
        if missing_templates:
            current_app.logger.warning(
                f'누락된 시뮬레이션 템플릿: {", ".join(missing_templates)}'
            )
        else:
            current_app.logger.info('모든 시뮬레이션 템플릿 확인 완료')
            
    except Exception as e:
        current_app.logger.error(f'시뮬레이션 템플릿 검증 오류: {e}')