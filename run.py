# run.py
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 개발 환경 기본 설정
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'dev-only-secret-key-do-not-use-in-production'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['CACHE_TYPE'] = 'simple'

print("======== sys.path ========")
for p in sys.path:
    print(p)
print("==========================")
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {current_dir}")

# app 디렉토리 존재 확인
app_dir = os.path.join(current_dir, 'app')
if not os.path.exists(app_dir):
    print(f"ERROR: 'app' directory not found at {app_dir}")
    sys.exit(1)

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)