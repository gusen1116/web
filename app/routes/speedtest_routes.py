# app/routes/speedtest_routes.py
from flask import Blueprint, render_template, current_app

speedtest_bp = Blueprint('speedtest', __name__, url_prefix='/speedtest')

@speedtest_bp.route('/')
def speedtest_page():
    """Render the network speed test page."""
    try:
        return render_template('speedtest.html')
    except Exception as e:
        current_app.logger.error(f'Speedtest 페이지 로드 에러: {e}')
        return render_template('500.html', error_message="Speedtest 페이지를 로드할 수 없습니다."), 500
