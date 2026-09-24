# 와구센 웹사이트 코드 분석 보고서

- 분석일: 2026-08-10
- 분석 대상: 현재 작업 디렉터리의 Flask 애플리케이션, Jinja 템플릿, JavaScript/CSS, 미디어 처리 코드, Python/Node 의존성
- 분석 방식: 소스 정적 분석, Flask 테스트 클라이언트 스모크 테스트, Python/JavaScript 문법 검사, 로컬 의존성 검사, 공개 이미지 GPS 메타데이터 읽기 전용 검사
- 주의: 분석 시작 시점부터 작업 트리에 수정·삭제·미추적 파일이 많이 있었습니다. 이 보고서는 커밋본이 아니라 **현재 보이는 작업 중 코드**를 기준으로 합니다. 기존 코드는 수정하지 않았습니다.
- 후속 수정: 2026-08-10에 400/403 템플릿 추가, 404/500 처리 보강, 누락 템플릿을 호출하던 URL 정리, 없는 게시글·시리즈의 404 복구를 완료했습니다. 아래 BUG-01·BUG-02·BUG-07 일부는 최초 분석 당시의 발견 기록입니다.

## 1. 한눈에 보는 결론

사이트의 기본 페이지, 블로그 목록·상세, 갤러리 목록·상세, 속도 측정 페이지는 동작합니다. 반면 보안상 먼저 막아야 할 문제와 실제 500 오류가 함께 존재합니다.

가장 먼저 처리할 항목은 다음과 같습니다.

1. 공개 포트 스캔 API가 사설 IP와 로컬 주소까지 검사할 수 있어 서버가 내부망 스캐너로 악용될 수 있습니다.
2. 갤러리 상세 경로에 `../`가 허용되어 갤러리 폴더 밖의 이미지를 읽고, 썸네일 폴더 밖에 JPEG 파일을 만들 가능성이 있습니다.
3. `run.py`가 항상 `debug=True`, `0.0.0.0`으로 실행되어 잘못 배포하면 Flask 디버거 노출 위험이 있습니다.
4. `npm start`가 Google Sheet의 모든 행을 지우도록 연결되어 있습니다.
5. HTML 정제 후 다시 속성을 안전하지 않게 조립해 저장형 XSS 방어를 우회할 수 있습니다.
6. 존재하지 않는 템플릿 때문에 공개 URL 6개 이상이 실제로 500을 반환합니다.
7. 속도 측정 업로드가 크기 제한 없이 요청 본문 전체를 메모리에 올리며, 다운로드·WHOIS·포트 스캔에 인증이나 속도 제한이 없습니다.
8. 이미지 원본이 매우 큽니다. 갤러리 원본 145MB, 게시글 이미지 116MB이며 게시글 이미지 22개 모두 1MB를 넘습니다.

권장 처리 순서는 **외부 악용 차단 → 500 오류 정리 → XSS/CSP 보강 → 미디어 최적화 → 중복/미사용 코드 정리 → 테스트 추가**입니다.

## 2. 심각도별 요약

| ID | 심각도 | 종류 | 요약 | 상태 |
|---|---|---|---|---|
| SEC-01 | P0 긴급 | SSRF/내부망 접근 | 공개 포트 스캐너가 사설·루프백 주소를 검사 가능 | 코드상 확인 |
| SEC-02 | P0 긴급 | 경로 이탈 | 갤러리 파일명으로 갤러리·썸네일 루트 밖 접근 가능 | 라우팅·경로 계산 확인 |
| OPS-01 | P0 긴급 | 운영 보안 | `run.py`가 항상 외부 바인딩 디버그 서버 실행 | 코드상 확인 |
| OPS-02 | P0 긴급 | 데이터 손실 | `npm start`가 Google Sheet 전체를 초기화 | 코드상 확인, 실행하지 않음 |
| SEC-03 | P1 높음 | 저장형 XSS | Bleach 처리 후 속성 재조립 과정에서 이벤트 속성 부활 | 안전한 문자열 테스트로 재현 |
| SEC-04 | P1 높음 | 메모리/대역폭 DoS | 무제한 업로드 메모리 적재, 최대 150MB 다운로드 반복 가능 | 코드상 확인 |
| BUG-01 | P1 높음 | 기능 장애 | 누락 템플릿과 예외 처리 때문에 여러 URL이 500 | 스모크 테스트 재현 |
| SEC-05 | P1 높음 | Host 헤더 오염 | 공격자 Host가 canonical, robots, sitemap에 반영 | 테스트로 재현 |
| SEC-06 | P1 높음 | DOM XSS | WHOIS 응답을 `innerHTML`에 직접 삽입 | 코드상 확인 |
| SEC-07 | P1 높음 | CSP 오설정 | `unsafe-inline`, 모든 HTTPS 출처 허용, 개발 출처가 운영 CSP에 섞임 | 운영 설정 테스트 확인 |
| PERF-01 | P1 높음 | 정적 자산 | 대형 원본 이미지를 카드·상세에서 그대로 제공 | 용량 측정 확인 |
| PERF-02 | P1 높음 | 서버 부하 | 모든 요청에서 게시글 파일을 여러 번 반복 파싱 | 호출 흐름 확인 |
| SEC-08 | P2 중간 | 세션/캐시 | 정적 파일과 robots/API 응답도 CSRF 세션 쿠키 생성 | 응답 헤더로 재현 |
| BUG-02 | P2 중간 | 날짜 | 날짜 없는 글의 mtime 대체 조건이 사실상 동작하지 않음 | 코드상 확인 |
| BUG-03 | P2 중간 | 개발 설정 | `FLASK_DEBUG=True`지만 Flask의 `DEBUG`는 False | 실행 설정 확인 |
| PERF-03 | P2 중간 | 캐시 | 갤러리 자산 URL에 매번 난수를 붙여 브라우저 캐시 무효화 | 템플릿 확인 |
| MAINT-01 | P2 중간 | 미사용 코드 | Sheets, ColorService, Assets 번들, 테스트 자산 등 정리 후보 다수 | 참조 검색 확인 |
| DEP-01 | P2 중간 | 재현성 | Python 의존성 버전 미고정, Node 의존성 미설치 | 로컬 검사 확인 |

## 3. 보안 취약점 상세

### SEC-01. 공개 포트 스캐너를 통한 SSRF·내부망 스캔·자원 고갈 — P0

**근거**

- `app/routes/utils_routes.py:19-25`의 검증은 DNS 해석 성공 여부만 확인합니다.
- `app/routes/utils_routes.py:46-126`은 사용자가 지정한 호스트와 최대 2,000개 포트를 서버에서 검사합니다.
- 요청 하나마다 `ThreadPoolExecutor(max_workers=200)`를 생성합니다.
- `app/routes/utils_routes.py:145-187`의 GET API도 동일하게 사용자가 지정한 호스트를 검사하며 CSRF조차 필요하지 않습니다.
- 루프백, RFC1918 사설망, 링크 로컬, 클라우드 메타데이터 주소, 멀티캐스트·예약 대역을 막는 코드가 없습니다.

**영향**

공격자가 이 웹 서버를 이용해 `127.0.0.1`, Docker/사내망, Redis·DB·관리 포트 등을 탐색할 수 있습니다. 동시에 여러 요청을 보내면 요청마다 200개 스레드와 최대 2,000개의 소켓이 생겨 서버가 멈출 수 있습니다. CSRF 토큰은 “해당 브라우저가 요청을 시작했는지”만 일부 확인할 뿐, 로그인·권한·속도 제한을 대신하지 않습니다.

**수정 권장**

1. 공개 기능이 꼭 필요하지 않다면 `/start_portscan`과 `/api/utils/port_scan`을 즉시 비활성화합니다.
2. 필요하다면 로그인된 관리자만 사용하도록 하고 IP별·계정별 rate limit을 둡니다.
3. DNS 결과를 한 번만 해석한 뒤 모든 A/AAAA 주소에 대해 `ipaddress.ip_address()`로 public/global 주소인지 검사합니다. 리디렉션이나 재해석 없이 검증한 IP에만 접속해야 DNS rebinding을 줄일 수 있습니다.
4. 포트는 `1..65535`로 제한하고 중복 제거 후 작은 상한(예: 50개)을 둡니다.
5. 요청별 스레드 풀을 만들지 말고 전역적으로 제한된 작업 큐를 사용합니다.
6. 감사 로그, 전체 작업 제한, 취소·타임아웃을 추가합니다.

### SEC-02. 갤러리 상세의 경로 이탈 및 썸네일 루트 밖 쓰기 — P0

**근거**

- `app/routes/gallery.py:39-42`가 `<path:filename>`을 받고 다시 `unquote()`하지만 안전한 파일명 검증을 하지 않습니다.
- `app/services/gallery_service.py:158-160`은 `os.path.join(photos_dir, filename)`만 사용합니다.
- `app/services/gallery_service.py:63-70`은 같은 파일명을 썸네일 경로에도 그대로 결합합니다.
- 라우터 검사에서 `/gallery/photo/../images/site/logo.png`가 실제로 `gallery.detail`에 매칭됐습니다.
- 해당 값의 원본 경로는 `app/static/images/site/logo.png`, 썸네일 경로는 `app/static/images/site/logo.jpg`로 계산되어 양쪽 모두 의도한 루트를 벗어났습니다.

**영향**

공격자는 서버에서 접근 가능한 “이미지 형식 파일”의 존재·EXIF·일부 메타데이터를 읽게 할 수 있습니다. 대상 썸네일이 없으면 GET 요청만으로 갤러리 썸네일 폴더 밖에 JPEG를 생성할 수도 있습니다. 권한과 파일 존재 상태에 따라 기존 애플리케이션 영역을 오염시킬 수 있습니다.

**수정 권장**

1. 상세 라우트를 `<filename>`으로 바꾸고 경로 구분자, `..`, URL 이중 디코딩을 거부합니다.
2. 목록에서 얻은 실제 파일 ID 집합에 포함된 값만 상세 조회에 허용하는 방식이 가장 단순합니다.
3. `Path(photos_dir).resolve()`와 `(root / filename).resolve()`의 `is_relative_to(root)`를 검사합니다.
4. 썸네일 경로도 별도로 같은 검사를 해야 합니다.
5. 사용자 파일명 대신 서버가 만든 불투명 ID를 URL에 쓰는 것도 좋습니다.

### OPS-01. 외부 바인딩 Flask 디버거 — P0

**근거**

- `run.py:39`가 환경과 무관하게 `app.run(debug=True, host='0.0.0.0', port=4000)`을 실행합니다.
- `run.py:10-14`는 SECRET_KEY가 없으면 고정 개발 키도 설정합니다.

**영향**

`python3 run.py`를 운영 서버에서 실행하거나 방화벽이 열린 개발 서버에서 실행하면 디버그 오류 화면과 재로더가 외부에 노출됩니다. Flask 디버거는 운영 환경에서 원격 코드 실행으로 이어질 수 있는 고위험 기능입니다. 고정 SECRET_KEY 사용 시 세션·CSRF 신뢰도도 무너집니다.

**수정 권장**

- `run.py`는 로컬 전용으로 `127.0.0.1`, `debug=app.debug`를 사용하고 운영 실행 경로와 분리합니다.
- 운영은 `gunicorn 'app:create_app("production")'` 같은 명시적 WSGI 명령만 허용합니다.
- 환경 파일 예시와 배포 명령을 README에 기록하고, 개발 키가 감지되면 외부 바인딩을 거부합니다.

### OPS-02. `npm start` 실행 시 Google Sheet 전체 삭제 — P0

**근거**

- `package.json:6-8`의 `start`는 `node sheets.js`입니다.
- `sheets.js:90-95`는 첫 작업으로 `sheet.clear()` 후 헤더를 교체합니다.
- `sheets.js:99-118`은 예제 데이터 추가·수정·삭제까지 자동 실행합니다.
- `sheets.js:127-128`에서 이 예제를 조건 없이 호출합니다.

**영향**

서비스 계정 권한이 있는 환경에서 평범한 `npm start` 한 번으로 지정된 스프레드시트 데이터가 삭제됩니다. 웹사이트 실행 명령으로 오해하기 쉬워 운영 사고 가능성이 매우 큽니다.

**수정 권장**

- 이 기능을 쓰지 않는다면 `sheets.js`, `package.json`, `package-lock.json`을 별도 실험 저장소로 옮기거나 삭제합니다.
- 유지한다면 라이브러리 코드와 CLI를 분리하고, 파괴적 예제는 테스트 전용 가짜 Sheet에서만 실행합니다.
- 삭제 작업에는 명시적 `--confirm-sheet-id`와 별도 환경 플래그를 요구하고 기본 실행에서는 절대 호출하지 않습니다.

### SEC-03. HTML 정제 후 속성 재조립으로 저장형 XSS 가능 — P1

**근거**

- `app/services/text_service.py:711-725`에서 Bleach로 먼저 HTML을 정제합니다.
- 그 뒤 `app/services/text_service.py:47-76`의 `URLLinkifyParser`가 HTML 속성값을 `f'{k}="{v}"'`로 이스케이프 없이 다시 조립합니다.
- 마지막에 `app/services/text_service.py:462-474`가 결과를 `Markup`으로 신뢰합니다.

읽기 전용 문자열 테스트로 다음 변환을 확인했습니다.

```text
입력/정제 결과: title="&quot; onmouseover=&quot;alert(1)"
최종 결과:      title="" onmouseover="alert(1)"
```

`img alt`에서도 같은 방식으로 `onerror`가 되살아났습니다.

**영향과 조건**

현재 공개 글 작성 API는 없어 일반 방문자가 바로 악용하기는 어렵습니다. 그러나 게시글 파일을 외부 입력·CMS·PR·자동 수집으로 받게 되거나 콘텐츠 저장소가 침해되면 저장형 XSS가 실행됩니다. 현재 CSP가 `unsafe-inline`을 허용하므로 이벤트 핸들러를 막아주지도 못합니다.

**수정 권장**

- 가장 좋은 방법은 URL 자동 링크화를 Markdown 변환 전 텍스트 단계에서 하거나, 검증된 DOM 라이브러리로 처리하는 것입니다.
- 직접 직렬화를 유지한다면 태그명·속성명 allowlist와 `html.escape(value, quote=True)`를 반드시 사용합니다.
- 더 안전하게는 “모든 변환 완료 후 Bleach 정제”를 마지막 단계로 옮기고 그 뒤에는 HTML 문자열을 다시 조립하지 않습니다.
- 이 페이로드를 회귀 테스트로 추가합니다.

### SEC-04. 속도 측정 엔드포인트의 메모리·대역폭 DoS — P1

**근거**

- `app/routes/speedtest_routes.py:64-70`은 CSRF를 면제하고 `request.get_data()`로 본문 전체를 메모리에 올립니다.
- 전역 `MAX_CONTENT_LENGTH`가 설정되어 있지 않습니다.
- `app/routes/speedtest_routes.py:30-56`은 인증 없이 요청당 최대 150MB를 스트리밍합니다.
- WHOIS, DNS, 포트 스캔, 속도 측정 모두 rate limit이 없습니다.

**영향**

큰 POST 여러 개로 프로세스 메모리를 소진하거나, 반복 다운로드로 서버·호스팅의 대역폭과 비용을 고갈시킬 수 있습니다. CSRF 면제 자체보다 인증·용량 제한·rate limit 부재가 핵심 문제입니다.

**수정 권장**

- `MAX_CONTENT_LENGTH`와 엔드포인트 전용 최대 크기를 설정합니다.
- 본문을 청크 단위로 읽되 상한을 넘으면 즉시 413을 반환합니다.
- IP별 동시 실행 수, 분당 실행 수, 하루 전송량을 제한합니다.
- CDN/리버스 프록시에서도 body size와 rate limit을 중복 적용합니다.
- 사용하지 않는 공개 진단 도구는 제거하거나 관리자 전용으로 전환합니다.

### SEC-05. Host 헤더 오염으로 canonical·robots·sitemap 변조 — P1

**근거**

- `app/templates/base.html:13,18`과 갤러리 base가 `request.base_url`을 canonical/OG URL로 사용합니다.
- `app/routes/main_routes.py:165-235`가 `_external=True` URL로 robots와 sitemap을 생성합니다.
- `TRUSTED_HOSTS`와 고정 `SERVER_NAME`이 설정되어 있지 않습니다.
- 테스트에서 `Host: attacker.example`을 보내자 홈 canonical, robots의 Sitemap, sitemap의 모든 URL에 공격자 호스트가 들어갔습니다.

**영향**

프록시·CDN 캐시 설정에 따라 검색 엔진 메타데이터가 공격자 도메인으로 오염되고 SEO 피싱·캐시 오염의 원인이 될 수 있습니다.

**수정 권장**

- Flask 3.1의 `TRUSTED_HOSTS`에 실제 도메인만 설정합니다.
- 공개 기준 URL을 설정 값(`PUBLIC_BASE_URL`)으로 고정해 sitemap/robots/canonical을 만듭니다.
- 프록시에서도 허용되지 않은 Host를 400 또는 444로 거부합니다.

### SEC-06. WHOIS 결과의 DOM XSS — P1

**근거**

- `app/static/js/speedtest.js:140-145`가 WHOIS 서버 응답 `val`을 템플릿 문자열로 만들어 `li.innerHTML`에 넣습니다.
- `app/static/js/speedtest.js:152-154`는 오류 메시지도 `innerHTML`로 넣습니다.

**영향**

WHOIS 응답은 외부 레지스트리/도메인 데이터입니다. 악의적 문자열이 포함되거나 중간 서비스가 변조되면 브라우저에서 HTML로 해석됩니다. 현재 완화된 CSP 때문에 인라인 이벤트도 실행될 수 있습니다.

**수정 권장**

`createElement()`와 `textContent`만 사용해 레이블·값·오류를 삽입합니다. 사용자·서버·외부 API에서 온 값은 `innerHTML`에 넣지 않는 규칙을 프로젝트 전체에 적용합니다.

### SEC-07. CSP가 사실상 완화되어 있고 개발 출처가 운영에도 포함됨 — P1

**근거**

- `app/app_config.py:53-76`에서 `script-src`가 `'unsafe-inline'`, 모든 `https:`, `data:`를 허용합니다.
- `frame-src`, `connect-src`도 모든 HTTPS 출처를 허용합니다.
- 요청마다 nonce를 만들지만(`app/__init__.py:71-74`) CSP 지시어에 nonce가 들어가지 않습니다.
- `DevelopmentConfig.CSP = Config.CSP.copy()`는 얕은 복사입니다. 이어지는 `connect-src.extend()`가 원본 리스트까지 바꿉니다.
- 운영 앱 테스트에서도 `http://0.0.0.0:4000`, `http://test.wagusen.com`이 CSP에 포함된 것을 확인했습니다.
- `ALLOWED_EXTERNAL_DOMAINS` 설정은 선언만 되어 있고 실제 콘텐츠 URL 검증에 사용되지 않습니다.

**영향**

XSS가 한 번 발생했을 때 CSP의 2차 방어 효과가 크게 떨어집니다. 임의 HTTPS 스크립트·프레임·연결을 허용하므로 공급망 공격이나 데이터 유출 방어 범위도 좁습니다.

**수정 권장**

- CSP 설정은 `copy.deepcopy()`하거나 환경별 완전한 불변 구조로 만듭니다.
- 인라인 `<style>`·`<script>`를 정적 파일로 옮기고 nonce 기반으로 전환한 뒤 `'unsafe-inline'`을 제거합니다.
- 외부 도메인은 정확한 호스트만 allowlist로 적고 `data:`는 필요한 지시어에만 둡니다.
- 외부 스크립트는 버전을 정확히 고정하고 가능하면 자체 호스팅/SRI를 사용합니다.

### SEC-08. 모든 응답에서 CSRF 세션을 생성해 캐시를 훼손 — P2

**근거**

- `app/__init__.py:76-82`의 함수명과 주석은 “CSRF cookie 설정”이지만 실제 `response.set_cookie()`는 없습니다.
- 대신 토큰이 없으면 `generate_csrf()`를 호출하여 Flask 세션을 만듭니다.
- 새 클라이언트로 `/static/css/core.css`, `/api/status`, `/robots.txt`를 요청했을 때 모두 `Set-Cookie`와 `Vary: Cookie`가 붙었습니다.
- 정적 CSS는 동시에 `Cache-Control: public, max-age=31536000`을 보냅니다.

**영향**

정적 파일·검색봇·상태 확인 요청까지 불필요한 세션 쿠키를 만들고 CDN/브라우저 캐시를 쿠키별로 분리하거나 캐시 불가 상태로 만들 수 있습니다. “JS가 읽는 CSRF 쿠키”도 실제로는 만들어지지 않습니다.

**수정 권장**

- 이 `after_request`를 제거하고 폼/HTML 렌더링 시에만 토큰을 만듭니다.
- SPA용 쿠키 패턴이 정말 필요하면 전용 엔드포인트와 명확한 쿠키 정책을 사용합니다.
- 정적 파일은 애플리케이션 세션 처리 밖에서 웹 서버/CDN이 제공하게 합니다.

### 그 밖의 보안 개선점

- `app/routes/speedtest_routes.py:19-23`은 아무 검증 없이 `X-Forwarded-For`를 신뢰하므로 사용자가 IP 표시를 조작할 수 있습니다. 신뢰 프록시에서만 `ProxyFix` 또는 서버 설정을 사용하십시오.
- `app/services/text_service.py:712`는 Bleach가 없으면 정제 없이 HTML을 반환하는 fail-open 구조입니다. 보안 필수 의존성이 없으면 시작을 실패시키는 fail-closed가 안전합니다.
- Markdown에서 임의 `iframe`과 모든 HTTP/HTTPS URL을 허용하지만 선언된 외부 도메인 allowlist는 쓰지 않습니다. 콘텐츠 작성자를 완전히 신뢰하지 않는다면 iframe을 제거하거나 호스트·sandbox를 강제하십시오.
- 운영 설정에서 `TALISMAN_FORCE_HTTPS`가 명시적으로 True가 아닙니다. 외부 프록시에서 HTTPS를 강제한다면 문서화하고, 그렇지 않으면 애플리케이션/프록시 중 한 곳에서 확실히 리디렉션하십시오.

## 4. 실제로 재현된 기능 버그

### BUG-01. 누락 템플릿 때문에 공개 페이지가 500 반환 — P1

다음 경로를 Flask 테스트 클라이언트로 호출해 실제 상태 코드를 확인했습니다.

| URL | 실제 결과 | 원인 |
|---|---:|---|
| `/network` | 500 | `network.html` 없음 |
| `/posts/tags` | 500 | `posts/tags_overview.html` 없음 |
| `/simulation/network` | 500 | `simulation/network.html` 없음 |
| `/simulation/gravity` | 500 | `simulation/gravity.html` 없음 |
| `/portscanner` | 500 | `port_scanner.html` 없음 |
| `/whois/` | 500 | `whois.html` 없음 |
| `/posts/!` | 500 | 400 처리기가 없는 `400.html` 렌더링 시도 |
| `/posts/images/bad!.jpg` | 500 | 403 처리기가 없는 `403.html` 렌더링 시도 |

현재 `speedtest.html`에 속도 측정·WHOIS·포트 스캔 UI가 통합되어 있으므로 `/network`, `/portscanner`, `/whois/`는 새 템플릿을 세 개 만드는 대신 `/speedtest/`로 리디렉션하거나 라우트를 제거하는 편이 단순합니다. `network`와 `gravity` 시뮬레이션은 카드에서 숨기거나 템플릿 구현 후 노출해야 합니다.

### BUG-02. 없는 게시글·시리즈가 404가 아니라 500 — P1

- `app/routes/posts_routes.py:167-202`의 넓은 `except Exception`이 내부 `abort(404)`까지 잡아 `abort(500)`으로 바꿉니다.
- `app/routes/posts_routes.py:290-311`의 시리즈 라우트도 같습니다.

`HTTPException`은 다시 발생시키거나, 예외 처리 범위를 실제 파일 파싱 부분으로 좁혀야 합니다. 사용자가 잘못된 URL을 입력한 것은 서버 장애가 아니므로 404가 유지되어야 합니다.

### BUG-03. 날짜 없는 글의 파일 수정 시각 대체가 동작하지 않음 — P2

`app/services/text_service.py:369-374`의 조건은 다음 이유로 사실상 항상 거짓입니다.

- `date`와 `created_at`의 `default_factory=datetime.now`가 각각 호출되어 값이 보통 서로 다릅니다.
- 설령 같아도 생성 직후의 값이 다시 호출한 `datetime.now()`보다 미래일 가능성은 거의 없습니다.

결과적으로 날짜 메타데이터가 없는 글은 요청할 때마다 “현재 시각”을 가져 정렬 순서와 sitemap `lastmod`가 불안정해질 수 있습니다. 파싱 단계에서 날짜 존재 여부를 명시적으로 기록하고, 없으면 무조건 파일 mtime을 사용하십시오.

### BUG-04. 개발 설정의 디버그 플래그가 Flask에 적용되지 않음 — P2

`app/app_config.py:186-190`은 `FLASK_DEBUG=True`를 설정하지만 Flask가 실제로 읽는 설정 키는 `DEBUG`입니다. 실행 확인 결과 `FLASK_DEBUG=True`, `app.debug=False`였습니다. `DevelopmentConfig.DEBUG = True`로 명확히 설정해야 합니다.

### BUG-05. 속도 측정 결과의 정확성과 오류 처리가 불완전 — P2

- `app/static/js/speedtest.js`는 `fetch()` 후 `response.ok`를 확인하지 않아 서버 400/500도 성공으로 계산할 수 있습니다.
- 다운로드 데이터는 반복되는 0 바이트라 프록시 압축에 매우 잘 압축되어 실제 회선보다 과장된 속도가 나올 수 있습니다.
- ping은 5회 중 최솟값만 표시해 일반적인 지연을 대표하지 못합니다.
- 브라우저 캐시 방지 쿼리/`Cache-Control: no-store, no-transform`이 없습니다.
- `NUM_PARALLEL_CONNECTIONS`는 선언만 하고 사용하지 않습니다.

응답 코드 검사, 취소 타임아웃, 캐시·압축 방지, 중앙값/평균 및 jitter 표기를 추가하십시오. “정확한 인터넷 속도”가 아니라 “브라우저에서 현재 서버까지의 HTTP 처리량”이라는 설명도 필요합니다.

### BUG-06. 테마 목록이 서버 HTML과 JavaScript에서 서로 다름 — P2

- `app/templates/base.html:41-49`와 갤러리 base는 8개 가까운 테마를 알고 있습니다.
- `app/static/js/main.js:7-11`은 light/dark/8bit 세 개만 관리합니다.
- 이전 테마 클래스 전체를 제거하지 않기 때문에 예전 `royal-*`, `cyberpixel` 클래스가 남은 상태에서 새 테마가 섞일 수 있습니다.

테마 정의를 한 곳의 JSON/JS 모듈로 통합하고, 알려진 모든 테마 클래스를 제거한 후 하나만 적용하십시오.

### BUG-07. 잘못된 정적 자산 경로 — P3

- `app/templates/about.html:6`은 존재하지 않는 `css/test.css`를 요청합니다.
- `app/templates/404.html:6`은 존재하지 않는 `static/img/icon/404.png`를 preload합니다. 실제 이미지는 `static/images/site/404.png`입니다.
- `app/__init__.py:64`의 Assets 번들은 존재하지 않는 `js/slide-minimal.js`를 포함합니다.

첫 두 항목은 브라우저에서 불필요한 404 요청을 만듭니다. Assets 번들은 현재 템플릿에서 사용되지 않아 당장 페이지를 깨지는 않지만, 나중에 빌드하면 실패할 수 있습니다.

### BUG-08. 사이트맵·상태 값의 하드코딩과 XML 생성 — P3

- 앱 버전 `2.0.0`이 설정과 `/api/status`에 중복 하드코딩되어 서로 어긋날 수 있습니다.
- 사이트맵은 최대 100개 글만 넣지만 설정상 글은 2,000개까지 허용합니다.
- XML을 문자열 연결로 만들며 XML escaping을 명시적으로 하지 않습니다.

버전은 설정 한 곳에서 가져오고, sitemap index 또는 50,000 URL 규격에 맞춰 전체 공개 글을 포함하십시오. XML 빌더나 Jinja XML 템플릿을 사용해 escaping을 보장하는 편이 안전합니다.

## 5. 성능 및 최적화

### PERF-01. 이미지 원본이 지나치게 큼 — P1

읽기 전용 용량 측정 결과입니다.

| 영역 | 파일 수 | 총 용량 | 특이 사항 |
|---|---:|---:|---|
| 갤러리 원본 | 26 | 145,014,375 bytes, 약 138MB | 5MB 초과 12개, 10MB 초과 3개 |
| 갤러리 썸네일 | 26 | 3,936,034 bytes, 약 3.8MB | 평균 약 151KB |
| 게시글 이미지 | 22 | 116,611,560 bytes, 약 111MB | 22개 모두 1MB 초과 |

갤러리 썸네일은 잘 분리되어 있지만 상세 페이지는 5~11MB 원본을 그대로 로드할 수 있습니다. 게시글 카드의 미리보기는 전용 썸네일 없이 `posts.serve_image`로 원본을 불러오므로 목록 몇 개만 봐도 수십 MB를 받을 수 있습니다.

**권장안**

- 업로드/반입 시 원본 보관용, 화면용(예: 1600~2400px), 카드용(400~800px)을 생성합니다.
- AVIF/WebP 변형과 `<picture>`, `srcset`, `sizes`를 사용합니다.
- 이미지에 `width`와 `height`를 기록해 CLS를 줄입니다.
- 홈의 로고·첫 주요 이미지는 `loading="lazy"` 대신 eager/fetchpriority를 검토합니다.
- 사진 파일은 Git/앱 프로세스가 아니라 오브젝트 스토리지+CDN으로 분리하는 것이 좋습니다.

### PERF-02. 게시글을 한 요청에서 여러 번 다시 읽고 파싱 — P1

`get_tags_count()`, `get_adjacent_posts()`, `get_series_posts()`가 각각 `get_all_text_posts()`를 다시 호출합니다.

- 홈: 전체 글 읽기 + 태그 집계를 위해 다시 읽기
- 블로그 목록: 전체 글 읽기 + 태그 집계를 위해 다시 읽기
- 글 상세: 글 검색, 태그, 이전/다음, 시리즈 처리를 위해 최대 여러 차례 전체 재읽기
- 각 호출은 파일 목록 조회, 디코딩 시도, 메타데이터 파싱, 정렬을 반복합니다.

현재 글 7개에서는 체감이 작지만 설정상 2,000개, 파일당 최대 10MB이므로 확장 시 급격히 느려집니다. 요청 단위로 한 번 읽은 목록을 전달하거나 `(path, mtime, size)` 기반 캐시/색인을 사용하십시오. 선언된 Redis/simple 캐시 설정은 실제 캐시 확장 초기화나 호출에 사용되지 않습니다.

### PERF-03. 갤러리에서 매 요청마다 정적 자산 캐시 키가 바뀜 — P2

`app/templates/gallery/base-gallery.html:53-56,74`가 CSS/JS URL에 `range(...)|random` 값을 붙입니다. 사용자가 새 페이지를 열 때마다 URL이 바뀌므로 1년 캐시 헤더가 있어도 브라우저는 다른 파일로 인식합니다.

기본 base의 `static_url()`처럼 파일 mtime 또는 빌드 해시를 사용하십시오. 내용이 바뀔 때만 URL이 바뀌어야 합니다.

### PERF-04. 갤러리 캐시 저장 방식의 확장성·동시성 문제 — P2

- 캐시 미스 사진마다 전체 JSON 캐시를 다시 저장하여 초기 생성이 O(n²) I/O가 됩니다.
- `threading.Lock`은 한 프로세스 안에서만 동작하므로 여러 Gunicorn worker가 같은 JSON을 동시에 쓸 수 있습니다.
- 키가 `filename_mtime`이라 파일이 바뀔 때 오래된 키가 제거되지 않습니다.
- 정적 폴더에 런타임 캐시를 쓰므로 읽기 전용 이미지/컨테이너 배포와 충돌할 수 있습니다.

한 번에 사진 전체를 처리하고 마지막에 원자적 `os.replace()`로 한 번 저장하거나 SQLite/Redis를 사용하십시오. 캐시는 `instance/` 또는 전용 writable 디렉터리에 두고 오래된 키를 정리하십시오.

### PERF-05. 전역 DOM 재작성과 관찰기 비용 — P2

모든 페이지에서 `mixtype.js`가 body의 텍스트를 문자 유형별 `<span>`으로 쪼개고 MutationObserver로 이후 변화도 다시 처리합니다. 동시에 `main.js`도 전체 이미지 MutationObserver, 모든 카드·버튼별 이벤트 리스너, 스크롤 시 반복 DOM 조회를 사용합니다.

글이 길거나 “더보기”로 카드가 계속 추가되면 DOM 노드 수와 관찰 비용이 커집니다. 먼저 CSS `font-family` fallback으로 해결 가능한지 확인하고, 꼭 필요한 영역에만 Mixtype을 적용하십시오. 스크롤 애니메이션은 IntersectionObserver 하나로 통합하고 이벤트 위임을 검토하십시오.

### PERF-06. 템플릿 안의 대형 인라인 CSS/JS — P3

`posts/view.html`은 약 18KB이며 상당 부분이 인라인 CSS입니다. `speedtest.html`, 시뮬레이션 템플릿에도 큰 스타일·스크립트가 들어 있습니다. 이는 HTML 캐시 재사용을 어렵게 하고 CSP에서 `unsafe-inline`을 제거하지 못하게 합니다.

페이지별 정적 CSS/JS 파일로 옮기고 mtime/콘텐츠 해시를 붙이면 브라우저 캐시, 코드 검색, CSP 강화가 모두 쉬워집니다.

## 6. 불필요하거나 정리 가능한 코드

아래는 바로 삭제하라는 의미가 아니라, 사용 의도를 확인한 뒤 정리할 후보입니다.

### 삭제/분리 우선 후보

1. **`sheets.js`, `package.json`, `package-lock.json`**: Flask 사이트와 연결점이 없고 `npm start`가 파괴적입니다. 별도 실험 프로젝트로 분리하는 것이 안전합니다.
2. **`app/services/color_service.py`와 `main_routes.py`의 `ColorService` import**: 서비스는 어떤 실행 코드에서도 사용되지 않습니다.
3. **Flask-Assets 번들**: `all_js`는 등록만 되고 어떤 템플릿에서도 사용되지 않습니다. 포함된 `slide-minimal.js`도 없습니다. 계속 안 쓴다면 `Flask-Assets`, `jsmin`, 등록 코드를 함께 제거할 수 있습니다.
4. **`app/static/js/test2.js`, `app/static/css/test2.css`, `app/static/typography_test.html`**: 현재 템플릿에서 참조되지 않는 실험/테스트 자산으로 보입니다. 개발 문서 폴더로 옮기거나 제거를 검토하십시오.
5. **누락 템플릿을 호출하는 오래된 라우트**: `/network`, `/portscanner`, `/whois/`는 이미 통합된 `/speedtest/`와 역할이 겹칩니다.
6. **`main_routes.py` 상단의 과거 수정 이력형 docstring**: 현재 코드의 책임보다 “이전에 무엇을 고쳤는지”를 설명합니다. Git 기록으로 옮기고 모듈 설명만 남기는 편이 좋습니다.

### 중복·죽은 설정

- `CACHE_TYPE`, Redis 주소, `CACHE_TIMEOUT`, `CACHE_MAX_SIZE`를 선언하지만 Flask-Caching을 설치·초기화·사용하지 않습니다.
- `SECURITY_HEADERS`는 선언되어 있지만 적용 코드가 없습니다.
- `ALLOWED_EXTERNAL_DOMAINS`는 선언되어 있지만 링크·iframe 검사에 사용되지 않습니다.
- `WTF_CSRF_EXEMPT_METHODS`는 실제 Flask-WTF의 보호 메서드 설정인 `WTF_CSRF_METHODS`를 바꾸지 않습니다. 실행 확인에서도 기본 `{POST, PUT, PATCH, DELETE}`가 그대로였습니다.
- `NUM_PARALLEL_CONNECTIONS`는 사용되지 않습니다.
- `routes/__init__.py`는 여러 blueprint를 다시 import하지만 앱 팩토리는 각 모듈에서 직접 import하고, simulation blueprint는 `__all__`에 없습니다. 한 방식을 선택하십시오.

### 코드 품질 개선

- 넓은 `except Exception`이 많아 실제 프로그래밍 오류와 정상적인 404/400까지 숨깁니다.
- 여러 곳의 `except: pass`는 장애 원인을 없애므로 예상 가능한 예외만 잡고 로그를 남겨야 합니다.
- 태그 URL을 문자열 `f'/posts/tag/{tag}'`로 만들지 말고 `url_for()`를 사용해 공백·한글·특수문자 인코딩을 보장하십시오.
- `os.path.abspath(...).startswith(root)`는 `/root2` 같은 접두 경로를 구분하지 못합니다. `Path.is_relative_to()` 또는 `os.path.commonpath()`를 사용하십시오.
- 에러 메시지에 `str(e)`를 그대로 사용자에게 보여 주는 부분(`posts_routes.py:99`)은 내부 경로·예외 정보를 노출할 수 있으므로 사용자용 문구와 로그를 분리하십시오.

## 7. 의존성·테스트·배포 상태

### 확인 결과

- 모든 Python 파일: 문법 검사 통과
- 모든 JavaScript 파일: `node --check` 통과
- `python3 -m pip check`: 깨진 로컬 Python 의존성 없음
- `npm ls --depth=0`: `google-auth-library`, `google-spreadsheet` 미설치로 실패
- 자동화된 단위/통합 테스트 디렉터리: 확인되지 않음
- Flask 스모크 테스트: 정상 페이지와 위 500 오류를 확인

### 문제점

1. `requirements.txt`의 모든 Python 패키지에 버전 범위가 없습니다. 새 배포 때 호환되지 않는 최신 버전이 설치될 수 있습니다.
2. 개발/테스트/운영 의존성 구분이 없습니다.
3. `TestingConfig.TEST_BASE_DIR`가 프로젝트 루트가 아니라 `/home/gusen` 방향으로 한 단계 더 올라가 `tests/test_posts` 경로가 잘못 계산됩니다.
4. README에는 설치, 환경 변수, 개발 실행, 운영 배포, 이미지 처리, 테스트 방법이 없습니다.
5. 현재 설정은 Flask 3.1.2에서 실행되지만 `FLASK_ENV`·`FLASK_DEBUG` 같은 오래된 방식과 Flask 설정 키가 섞여 있습니다.

### 권장안

- 검증한 최소/상한 버전을 명시하거나 lock 파일/constraints 파일을 사용합니다.
- `pytest`, Flask test client, 임시 posts/gallery 디렉터리를 이용한 테스트를 추가합니다.
- CI에서 Python 문법/린트, JS 문법, 템플릿 로딩, 보안 회귀 페이로드, 주요 URL 상태 코드를 검사합니다.
- 최소 회귀 테스트 대상: 경로 이탈, XSS 속성 페이로드, 사설 IP 거부, 없는 글 404, 모든 메뉴 URL 200/3xx, 정적 파일에 Set-Cookie 없음, 운영 CSP에 개발 주소 없음.

## 8. 잘 되어 있는 부분

문제만 있는 프로젝트는 아닙니다. 다음 부분은 방향이 좋습니다.

- 운영 SECRET_KEY가 개발 기본값이면 시작을 중단하는 검사가 있습니다.
- 세션 쿠키에 Secure/HttpOnly/SameSite 설정을 두고 Talisman·CSRFProtect·압축 확장을 사용합니다.
- 게시글 미디어 파일명 검증은 경로 구분자와 확장자를 제한하고 `send_from_directory`를 사용합니다.
- Markdown에 Bleach와 CSS sanitizer를 적용하려는 구조 자체는 좋습니다. 다만 마지막 재직렬화 순서만 고쳐야 합니다.
- 갤러리 목록은 원본 대신 별도 썸네일을 사용합니다.
- 이미지 반입 서비스는 임시 파일과 `os.replace()`를 사용해 원자적으로 옮기며, 안전한 파일명과 크기 상한을 둡니다.
- 공개 갤러리·게시글 이미지 48개를 읽기 전용 검사한 결과 GPS 메타데이터는 0개였고 검사 오류도 없었습니다.
- 외부 링크에 `noopener noreferrer`를 적용한 부분, Jinja 자동 이스케이프, 기본 보안 헤더 도입은 좋은 기반입니다.

## 9. 추천 작업 순서

### 1단계: 오늘 처리할 긴급 조치

1. 포트 스캔 두 엔드포인트를 비공개 또는 비활성화합니다.
2. 갤러리 파일명을 목록 allowlist로 제한하고 루트 경로 검사를 추가합니다.
3. `run.py`의 외부 디버그 실행을 제거합니다.
4. 파괴적인 Sheets 코드를 웹 프로젝트에서 분리하고 `npm start`를 막습니다.
5. 업로드 본문·다운로드 실행 횟수 제한을 프록시와 앱에 적용합니다.

### 2단계: 기능 안정화

1. 누락 템플릿 라우트를 제거·리디렉션·구현합니다.
2. 게시글/시리즈의 `abort()`가 500으로 바뀌지 않게 예외 처리를 고칩니다.
3. 400/403 템플릿을 추가하거나 공통 에러 템플릿을 사용합니다.
4. 잘못된 CSS/이미지 경로를 수정합니다.
5. 모든 메뉴와 공개 라우트에 상태 코드 스모크 테스트를 추가합니다.

### 3단계: 보안 강화

1. URL linkify 이후 최종 Bleach 정제를 적용해 XSS 우회를 막습니다.
2. WHOIS UI의 `innerHTML`을 `textContent`로 바꿉니다.
3. `TRUSTED_HOSTS`와 `PUBLIC_BASE_URL`을 설정합니다.
4. CSP를 deep copy하고 nonce/정확한 출처 allowlist로 좁힙니다.
5. 정적/API 응답에서 불필요한 CSRF 세션 생성을 제거합니다.

### 4단계: 성능·정리

1. 게시글 카드용 이미지 변형과 갤러리 상세용 화면 크기 이미지를 생성합니다.
2. 게시글 색인/캐시를 만들어 한 요청에서 파일을 한 번만 읽습니다.
3. 갤러리 난수 cache-buster를 파일 해시/mtime으로 교체합니다.
4. Mixtype 적용 범위를 줄이고 템플릿 인라인 CSS/JS를 정적 파일로 옮깁니다.
5. 미사용 Sheets/Assets/ColorService/테스트 자산과 죽은 설정을 정리합니다.

## 10. 분석의 한계

- 실제 운영 프록시, DNS, 방화벽, CDN, 컨테이너, 환경 변수는 제공되지 않아 애플리케이션 코드 기준으로 판단했습니다.
- 인터넷 기반 CVE/의존성 취약점 데이터베이스 조회는 수행하지 않았습니다. 버전 고정 후 `pip-audit`과 `npm audit`을 CI에서 추가로 실행해야 합니다.
- 실제 외부 포트 스캔, 대용량 공격, Google Sheet 실행 같은 위험한 검증은 하지 않았습니다.
- 브라우저 E2E·접근성 도구·Lighthouse 실측은 하지 않았습니다.

이 보고서에서 P0/P1 항목을 먼저 해결하면 보안 악용 가능성과 사용자에게 보이는 500 오류를 크게 줄일 수 있습니다.
