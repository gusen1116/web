#!/usr/bin/env python3
# debug_config.py - 설정 파일 위치 확인용
import os
import sys

print("=== 디버그 정보 ===")
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"스크립트 위치: {os.path.abspath(__file__)}")
print(f"\nPython 경로 (sys.path):")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

print("\n=== config 관련 파일 확인 ===")
web_dir = "/home/gusen/web"
files_to_check = ["config.py", "app_config.py"]

for filename in files_to_check:
    filepath = os.path.join(web_dir, filename)
    if os.path.exists(filepath):
        print(f"✓ {filepath} 존재함 (크기: {os.path.getsize(filepath)} bytes)")
    else:
        print(f"✗ {filepath} 존재하지 않음")

print("\n=== config 패키지 충돌 확인 ===")
try:
    import config
    print(f"config 모듈 위치: {config.__file__ if hasattr(config, '__file__') else 'built-in'}")
except ImportError as e:
    print(f"config 모듈을 import할 수 없음: {e}")

print("\n=== 해결 방법 테스트 ===")
sys.path.insert(0, web_dir)
print(f"sys.path에 {web_dir} 추가됨")

try:
    # config 모듈 다시 import 시도
    if 'config' in sys.modules:
        del sys.modules['config']
    import config
    print(f"✓ config 모듈 import 성공: {config.__file__ if hasattr(config, '__file__') else 'unknown'}")
    
    # config 딕셔너리가 있는지 확인
    if hasattr(config, 'config'):
        print(f"✓ config.config 찾음 (타입: {type(config.config)})")
        print(f"  사용 가능한 설정: {list(config.config.keys()) if isinstance(config.config, dict) else 'N/A'}")
    else:
        print("✗ config.config를 찾을 수 없음")
        
except Exception as e:
    print(f"✗ 오류 발생: {e}")
    import traceback
    traceback.print_exc()