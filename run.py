# run.py
import sys
import os
# 현재 작업 디렉토리와 프로젝트 루트를 sys.path에 추가 (필요한 경우)
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))) # 현재 파일(run.py)이 있는 디렉토리
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # 프로젝트 루트 (만약 run.py가 프로젝트 루트에 있다면 이 줄은 필요 없음)

print("======== sys.path ========")
for p in sys.path:
    print(p)
print("==========================")
print(f"Current working directory: {os.getcwd()}")

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)