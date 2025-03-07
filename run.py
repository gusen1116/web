# run.py
from app import create_app, socketio, db

app = create_app()

# 앱 컨텍스트에서 모델 임포트 확인
with app.app_context():
    from app.models import User, Category, Tag, Post, PostTag
    
    # 개발용: 기본 사용자 생성 (필요시)
    # 첫 실행 시 주석 해제하여 기본 사용자 생성
    """
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
    """

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)