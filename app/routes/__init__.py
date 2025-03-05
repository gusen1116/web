from app.routes.main_routes import main_bp
from app.routes.auth_routes import auth_bp
from app.routes.blog_routes import blog_bp

# 라우트 블루프린트들을 내보내기
__all__ = ['main_bp', 'auth_bp', 'blog_bp']