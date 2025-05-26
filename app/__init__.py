# app/__init__.py
from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from app.config import Config

# CSRF 보호 전역 객체
csrf = CSRFProtect()

def create_app(config_object: Optional[object] = None) -> Flask:
    """
    Flask 애플리케이션 팩토리 함수
    
    Args:
        config_object: 설정 객체 (기본값: Config)
    
    Returns:
        Flask: 구성된 Flask 애플리케이션 인스턴스
    """
    app = Flask(__name__, instance_relative_config=False)
    
    # 설정 로드 - 단순화된 설정 시스템
    _configure_app(app, config_object)
    
    # 확장 프로그램 초기화
    _init_extensions(app)
    
    # 블루프린트 등록 (수정된 부분)
    _register_blueprints(app)
    
    # 필요한 디렉토리 생성
    _create_directories(app)
    
    # 에러 핸들러 등록
    _register_error_handlers(app)
    
    # 보안 헤더 설정
    _configure_security_headers(app)
    
    # 로깅 설정
    _configure_logging(app)
    
    return app

def _configure_app(app: Flask, config_object: Optional[object]) -> None:
    """애플리케이션 설정 구성 - 단순화"""
    # 기본 설정 로드
    app.config.from_object(Config)
    
    # 사용자 정의 설정이 있으면 적용
    if config_object:
        app.config.from_object(config_object)
    
    app.logger.info('애플리케이션 설정 완료')

def _init_extensions(app: Flask) -> None:
    """Flask 확장 프로그램 초기화"""
    csrf.init_app(app)

def _register_blueprints(app: Flask) -> None:
    """
    블루프린트 등록 - Flask 2.2+ 호환성 개선
    
    주요 변경사항:
    - before_app_first_request 제거 대응
    - 시뮬레이션 템플릿 검증을 직접 호출로 변경
    """
    try:
        from app.routes.main_routes import main_bp
        # 시뮬레이션 블루프린트와 템플릿 검증 함수를 함께 import
        from app.routes.simulation import simulation_bp, verify_simulation_templates
        from app.routes.posts_routes import posts_bp
        
        # 각 블루프린트를 애플리케이션에 등록
        app.register_blueprint(main_bp)
        app.register_blueprint(simulation_bp)
        app.register_blueprint(posts_bp)
        
        # Flask 2.2+ 호환성: 애플리케이션 초기화 완료 후 템플릿 검증 실행
        # 이전에는 @before_app_first_request 데코레이터를 사용했지만
        # 최신 Flask에서는 제거되었으므로 직접 호출
        verify_simulation_templates(app)
        
        app.logger.info('모든 블루프린트 등록 완료')
    except ImportError as e:
        app.logger.error(f'블루프린트 등록 실패: {e}')
        raise

def _create_directories(app: Flask) -> None:
    """필요한 디렉토리 생성 - 업로드 디렉토리 제외"""
    directories = [
        app.config.get('POSTS_DIR'),
        'logs'  # 로그 디렉토리만 생성
    ]
    
    for directory in directories:
        if directory:
            try:
                os.makedirs(directory, exist_ok=True)
                app.logger.debug(f'디렉토리 생성/확인: {directory}')
            except OSError as e:
                app.logger.error(f'디렉토리 생성 실패 {directory}: {e}')

def _register_error_handlers(app: Flask) -> None:
    """에러 핸들러 등록"""
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f'400 에러: {request.url} - {error}')
        return render_template('400.html', error=error), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning(f'403 에러: {request.url} - {error}')
        return render_template('403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found(error):
        # 404는 일반적이므로 info 레벨로 기록
        app.logger.info(f'404 에러: {request.url}')
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'500 에러: {request.url} - {error}')
        return render_template('500.html'), 500

def _configure_security_headers(app: Flask) -> None:
    """보안 헤더 설정 - 항상 프로덕션 수준으로 적용"""
    
    @app.after_request
    def set_security_headers(response):
        # 기본 보안 헤더들
        security_headers = app.config.get('SECURITY_HEADERS', {})
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # CSP 헤더 - 엄격한 보안 정책
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "media-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'self'"
        )
        
        return response

def _configure_logging(app: Flask) -> None:
    """로깅 설정 - 항상 프로덕션 수준"""
    # 로그 디렉토리 생성
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # 파일 로그 핸들러 설정
    file_handler = RotatingFileHandler(
        'logs/wagusen.log', 
        maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),  # 10MB
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
    )
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # 로그 레벨 설정
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    file_handler.setLevel(log_level)
    
    # 애플리케이션 로거에 핸들러 추가
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    
    # 외부 라이브러리 로그 레벨 조정 (노이즈 감소)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    app.logger.info('와구센 애플리케이션 시작')