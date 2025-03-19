# app/routes/__init__.py
from app.routes.main_routes import main_bp
from app.routes.blog_routes import blog_bp
from app.routes.simulation import simulation_bp

# 라우트 블루프린트들을 내보내기
__all__ = ['main_bp', 'auth_bp', 'blog_bp', 'simulation_bp']