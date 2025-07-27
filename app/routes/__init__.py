# app/routes/__init__.py
from .main_routes import main_bp
from .posts_routes import posts_bp
from .gallery import gallery_bp
from .speedtest_routes import speedtest_bp
from .whois_routes import whois_bp
from .utils_routes import utils_bp

# 내보낼 블루프린트 목록
__all__ = [
    'main_bp', 
    'posts_bp',
    'gallery_bp',
    'speedtest_bp',
    'whois_bp',
    'utils_bp'
]