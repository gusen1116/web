# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.services.auth_service import google_oauth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 로그인 로직 구현
    pass

@auth_bp.route('/google-login')
def google_login():
    # 구글 OAuth 로그인 로직 구현
    return google_oauth.authorize()

@auth_bp.route('/google-callback')
def google_callback():
    # 구글 OAuth 콜백 로직 구현
    user_info = google_oauth.callback()
    # 사용자 정보 처리 및 로그인
    return redirect(url_for('main.index'))