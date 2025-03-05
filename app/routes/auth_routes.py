# app/routes/auth_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 로그인 로직 구현
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('auth/register.html')

@auth_bp.route('/google-login')
def google_login():
    # 구글 로그인 구현
    from app.services.auth_service import google_login as google_login_service
    return google_login_service()

@auth_bp.route('/google-callback')
def google_callback():
    # 구글 OAuth 콜백 로직 구현
    from app.services.auth_service import google_callback as google_callback_service
    return google_callback_service()

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')