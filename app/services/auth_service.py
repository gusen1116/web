# app/services/auth_service.py
from flask import url_for, session, redirect, request, current_app
from authlib.integrations.flask_client import OAuth
from flask_login import login_user
from app import db

# OAuth 객체를 전역으로 생성
oauth = OAuth()

def init_oauth(app):
    """앱 객체가 있을 때 OAuth 초기화"""
    oauth.init_app(app)
    
    # 구글 OAuth 앱 설정
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'email profile'},
    )

def google_login():
    """구글 로그인 처리"""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

def google_callback():
    """구글 OAuth 콜백 처리"""
    token = oauth.google.authorize_access_token()
    resp = oauth.google.get('userinfo')
    user_info = resp.json()
    
    # 이미 등록된 사용자인지 확인
    from app.models.user import User
    user = User.query.filter_by(google_id=user_info['id']).first()
    
    # 등록되지 않은 사용자면 새로 생성
    if not user:
        user = User(
            username=user_info['name'],
            email=user_info['email'],
            google_id=user_info['id']
        )
        db.session.add(user)
        db.session.commit()
    
    # 사용자 로그인
    login_user(user)
    return redirect(url_for('main.index'))