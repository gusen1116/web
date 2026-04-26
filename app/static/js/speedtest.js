/**
 * 네트워크 진단 도구 JavaScript (최종 통합 버전)
 * - 속도 테스트, WHOIS 조회, 포트 스캔 기능 통합
 */
(function() {
    'use strict';

    // ===============================================
    //               전역 설정 및 요소 참조
    // ===============================================
    const DOWNLOAD_TOTAL_SIZE_MB = 50; // 테스트 시간 단축을 위해 조정
    const UPLOAD_TOTAL_SIZE_MB = 20;
    const NUM_PARALLEL_CONNECTIONS = 2;

    // DOM 요소
    const el = {
        // Speedtest
        startTestBtn: document.getElementById('startTestBtn'),
        speedResults: document.getElementById('speedResults'),
        pingResult: document.getElementById('pingResult'),
        downloadResult: document.getElementById('downloadResult'),
        uploadResult: document.getElementById('uploadResult'),
        speedProgress: document.getElementById('speedProgressContainer'),
        speedBar: document.getElementById('speedProgressBar'),

        // WHOIS
        whoisInput: document.getElementById('whoisInput'),
        whoisBtn: document.getElementById('whoisBtn'),
        whoisResult: document.getElementById('whoisResult'),
        whoisList: document.getElementById('whoisList'),
        whoisRaw: document.getElementById('whoisRaw'),

        // Port Scan
        portHost: document.getElementById('portHost'),
        portList: document.getElementById('portList'),
        portBtn: document.getElementById('portBtn'),
        portProgress: document.getElementById('portProgressContainer'),
        portBar: document.getElementById('portProgressBar'),
        portTerminal: document.getElementById('portTerminal')
    };

    // CSRF 토큰 헬퍼
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }

    // ===============================================
    //               Speedtest 로직
    // ===============================================
    async function runSpeedtest() {
        if (!el.startTestBtn) return;

        // 초기화
        el.startTestBtn.disabled = true;
        el.startTestBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 테스트 중...';
        el.speedResults.style.display = 'block';
        el.speedProgress.style.display = 'block';
        el.pingResult.textContent = '...';
        el.downloadResult.textContent = '...';
        el.uploadResult.textContent = '...';

        try {
            // 1. Ping
            const latencies = [];
            for (let i = 0; i < 5; i++) {
                const start = performance.now();
                await fetch('/speedtest/ping_target');
                latencies.push(performance.now() - start);
                el.pingResult.textContent = `${Math.min(...latencies).toFixed(1)} ms`;
            }

            // 2. Download
            el.speedBar.style.width = '10%';
            const dlStart = performance.now();
            const dlResponse = await fetch(`/speedtest/download?size_mb=${DOWNLOAD_TOTAL_SIZE_MB}`);
            const reader = dlResponse.body.getReader();
            let dlBytes = 0;
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                dlBytes += value.length;
                const progress = (dlBytes / (DOWNLOAD_TOTAL_SIZE_MB * 1024 * 1024)) * 100;
                el.speedBar.style.width = `${10 + (progress * 0.4)}%`;
            }
            const dlDuration = (performance.now() - dlStart) / 1000;
            const dlMbps = ((dlBytes * 8) / dlDuration / 1000000).toFixed(2);
            el.downloadResult.textContent = dlMbps;

            // 3. Upload
            el.speedBar.style.width = '60%';
            const ulData = new Uint8Array(UPLOAD_TOTAL_SIZE_MB * 1024 * 1024);
            const ulStart = performance.now();
            await fetch('/speedtest/upload', {
                method: 'POST',
                body: ulData,
                headers: { 'X-CSRFToken': getCsrfToken() }
            });
            const ulDuration = (performance.now() - ulStart) / 1000;
            const ulMbps = ((ulData.length * 8) / ulDuration / 1000000).toFixed(2);
            el.uploadResult.textContent = ulMbps;
            el.speedBar.style.width = '100%';

        } catch (err) {
            console.error('Speedtest Error:', err);
            alert('속도 측정 중 오류가 발생했습니다.');
        } finally {
            el.startTestBtn.disabled = false;
            el.startTestBtn.innerHTML = '테스트 시작';
            setTimeout(() => el.speedProgress.style.display = 'none', 1000);
        }
    }

    // ===============================================
    //               WHOIS 로직
    // ===============================================
    async function runWhois() {
        const domain = el.whoisInput.value.trim();
        if (!domain) return;

        el.whoisBtn.disabled = true;
        el.whoisResult.style.display = 'block';
        el.whoisList.innerHTML = '<li>조회 중...</li>';
        el.whoisRaw.style.display = 'none';

        try {
            const response = await fetch(`/whois/api/${domain}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || '조회 실패');

            el.whoisList.innerHTML = '';
            const keys = {
                domain_name: '도메인',
                registrar: '등록기관',
                creation_date: '등록일',
                expiration_date: '만료일',
                status: '상태'
            };

            for (const [key, label] of Object.entries(keys)) {
                if (data[key]) {
                    const val = Array.isArray(data[key]) ? data[key][0] : data[key];
                    const li = document.createElement('li');
                    li.innerHTML = `<span class="info-label">${label}</span> <span>${val}</span>`;
                    el.whoisList.appendChild(li);
                }
            }

            el.whoisRaw.style.display = 'block';
            el.whoisRaw.textContent = data.text || JSON.stringify(data, null, 2);

        } catch (err) {
            el.whoisList.innerHTML = `<li style="color:red;">오류: ${err.message}</li>`;
        } finally {
            el.whoisBtn.disabled = false;
        }
    }

    // ===============================================
    //               Port Scan 로직
    // ===============================================
    async function runPortScan() {
        const host = el.portHost.value.trim();
        let ports;
        try {
            ports = JSON.parse(el.portList.value);
        } catch(e) {
            ports = el.portList.value.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p));
        }

        if (!host || !ports.length) return;

        el.portBtn.disabled = true;
        el.portTerminal.style.display = 'block';
        el.portProgress.style.display = 'block';
        el.portBar.style.width = '0%';
        el.portTerminal.innerHTML = `<div style="color:#888;">[SYSTEM] Scanning ${host}...</div>`;

        try {
            const response = await fetch('/start_portscan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ host, ports })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.substring(6));
                        if (data.port && data.status === 'Open') {
                            const div = document.createElement('div');
                            div.innerHTML = `<span style="color:#00ff00;">[OPEN]</span> Port ${data.port}`;
                            el.portTerminal.appendChild(div);
                            el.portTerminal.scrollTop = el.portTerminal.scrollHeight;
                        }
                        if (data.progress) {
                            el.portBar.style.width = `${data.progress.percentage}%`;
                        }
                    }
                }
            }
            const fin = document.createElement('div');
            fin.innerHTML = `<div style="color:#888; margin-top:0.5rem;">[SYSTEM] Scan completed.</div>`;
            el.portTerminal.appendChild(fin);

        } catch (err) {
            el.portTerminal.innerHTML += `<div style="color:red;">[ERROR] ${err.message}</div>`;
        } finally {
            el.portBtn.disabled = false;
            setTimeout(() => el.portProgress.style.display = 'none', 2000);
        }
    }

    // ===============================================
    //               이벤트 리스너 연결
    // ===============================================
    if (el.startTestBtn) el.startTestBtn.addEventListener('click', runSpeedtest);
    if (el.whoisBtn) el.whoisBtn.addEventListener('click', runWhois);
    if (el.whoisInput) el.whoisInput.addEventListener('keypress', e => e.key === 'Enter' && runWhois());
    if (el.portBtn) el.portBtn.addEventListener('click', runPortScan);

})();
