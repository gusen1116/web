# app/services/auth_service.py
from flask import url_for, session, redirect, request
from authlib.integrations.flask_client import OAuth
from app import app, db
from app.models.user import User
from flask_login import login_user, logout_user, login_required, current_user
oauth = OAuth(app)

google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_CLIENT_ID'),
    consumer_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
    request_token_params={
        'scope': 'email profile'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

def google_login():
    return google.authorize(callback=url_for('auth.google_callback', _external=True))

def google_callback():
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    
    session['google_token'] = (resp['access_token'], '')
    user_info = google.get('userinfo')
    
    # 이미 등록된 사용자인지 확인
    user = User.query.filter_by(google_id=user_info.data['id']).first()
    
    # 등록되지 않은 사용자면 새로 생성
    if not user:
        user = User(
            username=user_info.data['name'],
            email=user_info.data['email'],
            google_id=user_info.data['id']
        )
        db.session.add(user)
        db.session.commit()
    
    # 사용자 로그인
    login_user(user)
    return redirect(url_for('main.index'))