/**
 * 네트워크 진단 도구 JavaScript
 * - 속도 테스트, 핑, Whois, 포트 스캔 기능 구현
 */
(function() {
    'use strict';

    // ===============================================
    //               전역 변수 및 상수
    // ===============================================
    const API_PREFIX = window.location.pathname.endsWith('/') ? window.location.pathname.slice(0, -1) : window.location.pathname;
    const PING_COUNT = 10;
    const DOWNLOAD_TOTAL_SIZE_MB = 150;
    const UPLOAD_TOTAL_SIZE_MB = 150;
    const NUM_PARALLEL_CONNECTIONS = 4;

    // DOM 요소 참조
    // Speedtest & Ping
    const startTestBtn = document.getElementById('startTestBtn');
    const resultsSection = document.getElementById('resultsSection');
    const pingResult = document.getElementById('pingResult');
    const jitterResult = document.getElementById('jitterResult');
    const downloadResult = document.getElementById('downloadResult');
    const uploadResult = document.getElementById('uploadResult');
    const clientIp = document.getElementById('clientIp');
    const testTimestamp = document.getElementById('testTimestamp');
    const downloadDataSize = document.getElementById('downloadDataSize');
    const uploadDataSize = document.getElementById('uploadDataSize');
    const speedtestErrorMessage = document.getElementById('speedtestErrorMessage');
    const downloadProgressBar = document.getElementById('downloadProgressBar');
    const downloadProgressContainer = document.getElementById('downloadProgressContainer');
    const uploadProgressBar = document.getElementById('uploadProgressBar');
    const uploadProgressContainer = document.getElementById('uploadProgressContainer');

    // Whois 조회
    const whoisDomainInput = document.getElementById('whoisDomainInput');
    const whoisSearchBtn = document.getElementById('whoisSearchBtn');
    const whoisResultCard = document.getElementById('whoisResultCard');
    const whoisResultContent = document.getElementById('whoisResultContent');
    const whoisErrorMessage = document.getElementById('whoisErrorMessage');

    // 포트 스캔
    const portScanHostInput = document.getElementById('portScanHostInput');
    const portScanPortsInput = document.getElementById('portScanPortsInput');
    const portScanBtn = document.getElementById('portScanBtn');
    const portScanResultCard = document.getElementById('portScanResultCard');
    const portScanResultContent = document.getElementById('portScanResultContent');
    const portScanErrorMessage = document.getElementById('portScanErrorMessage');

    let eventSource = null;

    // ===============================================
    //               Speedtest & Ping
    // ===============================================
    function updatePingUI(value, jitterVal) {
        if (!pingResult || !jitterResult) return;
        pingResult.textContent = value;
        jitterResult.textContent = jitterVal;
    }

    function updateUIPercentage(progressBarElement, progressPercent) {
        if (!progressBarElement) return;
        const percent = Math.min(100, Math.max(0, progressPercent)).toFixed(0);
        progressBarElement.style.width = `${percent}%`;
        progressBarElement.textContent = `${percent}%`;
    }

    function updateDownloadUI(speedMbps, progressPercent) {
        if (!downloadResult || !downloadProgressBar || !downloadProgressContainer) return;
        downloadResult.textContent = speedMbps;
        if (typeof progressPercent === 'number') {
            updateUIPercentage(downloadProgressBar, progressPercent);
        }
        if (speedMbps !== '측정 중...' && speedMbps !== '실패') {
            downloadProgressContainer.style.display = 'none';
        } else if (speedMbps === '측정 중...') {
            downloadProgressContainer.style.display = 'block';
            downloadProgressBar.classList.remove('error');
        }
    }

    function updateUploadUI(speedMbps, progressPercent) {
        if (!uploadResult || !uploadProgressBar || !uploadProgressContainer) return;
        uploadResult.textContent = speedMbps;
        if (typeof progressPercent === 'number') {
            updateUIPercentage(uploadProgressBar, progressPercent);
        }
        if (speedMbps !== '측정 중...' && speedMbps !== '실패') {
            uploadProgressContainer.style.display = 'none';
        } else if (speedMbps === '측정 중...') {
            uploadProgressContainer.style.display = 'block';
            uploadProgressBar.classList.remove('error');
        }
    }

    function showSpeedtestError(message) {
        if (!speedtestErrorMessage) return;
        speedtestErrorMessage.textContent = message;
        speedtestErrorMessage.classList.add('visible');
    }

    function resetSpeedtestUI() {
        if (!speedtestErrorMessage || !downloadProgressBar || !uploadProgressBar) return;
        
        speedtestErrorMessage.textContent = '';
        speedtestErrorMessage.classList.remove('visible');
        updatePingUI('-', '-');
        updateDownloadUI('-', 0);
        downloadProgressBar.classList.remove('error');
        downloadProgressContainer.style.display = 'none';

        updateUploadUI('-', 0);
        uploadProgressBar.classList.remove('error');
        uploadProgressContainer.style.display = 'none';

        clientIp.textContent = '-';
        downloadDataSize.textContent = '-';
        uploadDataSize.textContent = '-';
        testTimestamp.textContent = '-';
    }

    function setSpeedtestButtonState(testing) {
        if (!startTestBtn) return;
        startTestBtn.disabled = testing;
        startTestBtn.innerHTML = testing ?
            '<i class="fas fa-spinner fa-spin"></i> 테스트 진행 중...' :
            '<i class="fas fa-play"></i> 속도/핑 테스트 시작';
    }

    async function getClientIpFromServer() {
        if (!clientIp) return;
        
        const url = `${API_PREFIX}/ip`;
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`IP 주소 확인 실패: ${response.status}`);
            const data = await response.json();
            clientIp.textContent = data.ip || '확인 불가';
        } catch (error) {
            clientIp.textContent = '확인 실패';
            showSpeedtestError(`IP 주소 확인 중 오류: ${error.message}`);
            throw error;
        }
    }

    async function testPing() {
        updatePingUI('측정 중...', '-');
        let latencies = [];
        for (let i = 0; i < PING_COUNT; i++) {
            const startTime = performance.now();
            const url = `${API_PREFIX}/ping_target?t=${Date.now()}&i=${i}`;
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`Ping 요청 실패: ${response.status}`);
                latencies.push(performance.now() - startTime);
            } catch (error) {
                latencies.push(5000); // 실패 시 높은 값
            }
            updatePingUI(`측정 중... (${((i + 1) / PING_COUNT * 100).toFixed(0)}%)`, '-');
            if (i < PING_COUNT - 1) await new Promise(resolve => setTimeout(resolve, 200));
        }

        if (latencies.length === 0) {
            updatePingUI('실패', '실패');
            throw new Error("모든 Ping 테스트에 실패했습니다.");
        }
        if (latencies.length > 3) latencies = latencies.sort((a, b) => a - b).slice(1, -1);
        
        const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
        let jitter = 0;
        if (latencies.length > 1) {
            jitter = Math.sqrt(latencies.map(l => Math.pow(l - avgLatency, 2)).reduce((a, b) => a + b, 0) / (latencies.length - 1));
        }
        
        if (isNaN(avgLatency) || isNaN(jitter)) {
            updatePingUI('오류', '오류');
            throw new Error("Ping/Jitter 값 계산 실패");
        }
        updatePingUI(avgLatency.toFixed(2), jitter.toFixed(2));
        return avgLatency;
    }

    async function testDownloadSpeed() {
        updateDownloadUI('측정 중...', 0);
        const CHUNK_SIZE_MB = DOWNLOAD_TOTAL_SIZE_MB / NUM_PARALLEL_CONNECTIONS;
        let totalBytesDownloaded = 0;
        downloadDataSize.textContent = DOWNLOAD_TOTAL_SIZE_MB;
        const startTime = performance.now();

        const downloadPromises = Array.from({ length: NUM_PARALLEL_CONNECTIONS }, (_, i) => {
            const url = `${API_PREFIX}/download?size_mb=${CHUNK_SIZE_MB}&r=${Date.now()}&c=${i}`;
            return fetch(url).then(async response => {
                if (!response.ok) throw new Error(`다운로드 청크 ${i} 실패: ${response.status}`);
                const reader = response.body.getReader();
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    totalBytesDownloaded += value.length;
                    const overallProgress = (totalBytesDownloaded / (DOWNLOAD_TOTAL_SIZE_MB * 1024 * 1024)) * 100;
                    updateDownloadUI('측정 중...', overallProgress);
                }
            });
        });

        try {
            await Promise.all(downloadPromises);
            const durationSeconds = (performance.now() - startTime) / 1000;
            if (durationSeconds <= 0.01) throw new Error("시간 측정 오류");
            const speedMbps = ((totalBytesDownloaded * 8) / durationSeconds / 1000000).toFixed(2);
            updateDownloadUI(speedMbps, 100);
            return parseFloat(speedMbps);
        } catch (error) {
            updateDownloadUI('실패', 0);
            downloadProgressBar.classList.add('error');
            downloadProgressBar.textContent = '실패';
            throw error;
        }
    }

    async function testUploadSpeed() {
        updateUploadUI('측정 중...', 0);
        const CHUNK_SIZE_BYTES = Math.floor((UPLOAD_TOTAL_SIZE_MB / NUM_PARALLEL_CONNECTIONS) * 1024 * 1024);
        const TOTAL_BYTES_TO_UPLOAD = UPLOAD_TOTAL_SIZE_MB * 1024 * 1024;
        let totalBytesUploadedSuccessfully = 0;
        uploadDataSize.textContent = UPLOAD_TOTAL_SIZE_MB;

        const randomDataChunk = new Uint8Array(CHUNK_SIZE_BYTES);
        const dataBlob = new Blob([randomDataChunk], { type: 'application/octet-stream' });

        const startTime = performance.now();
        const uploadPromises = Array.from({ length: NUM_PARALLEL_CONNECTIONS }, (_, i) =>
            new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                const url = `${API_PREFIX}/upload?r=${Date.now()}&c=${i}`;
                xhr.open('POST', url, true);
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        totalBytesUploadedSuccessfully += CHUNK_SIZE_BYTES; 
                        const overallProgress = (totalBytesUploadedSuccessfully / TOTAL_BYTES_TO_UPLOAD) * 100;
                        updateUploadUI('측정 중...', overallProgress);
                        resolve();
                    } else {
                        reject(new Error(`업로드 청크 ${i} 실패: ${xhr.status}`));
                    }
                };
                xhr.onerror = () => reject(new Error(`업로드 청크 ${i} 네트워크 오류`));
                xhr.send(dataBlob);
            })
        );

        try {
            await Promise.all(uploadPromises);
            const durationSeconds = (performance.now() - startTime) / 1000;
            if (durationSeconds <= 0.01) throw new Error("시간 측정 오류");
            const speedMbps = ((totalBytesUploadedSuccessfully * 8) / durationSeconds / 1000000).toFixed(2);
            updateUploadUI(speedMbps, 100); 
            return parseFloat(speedMbps);
        } catch (error) {
            updateUploadUI('실패', Math.max(0, (totalBytesUploadedSuccessfully / TOTAL_BYTES_TO_UPLOAD) * 100)); 
            uploadProgressBar.classList.add('error');
            uploadProgressBar.textContent = '실패';
            throw error;
        }
    }

    // ===============================================
    //               Whois Lookup
    // ===============================================
    function setWhoisButtonState(searching) {
        if (!whoisSearchBtn) return;
        whoisSearchBtn.disabled = searching;
        whoisSearchBtn.innerHTML = searching ? '<i class="fas fa-spinner fa-spin"></i> 조회 중...' : '<i class="fas fa-search"></i> 조회';
    }

    function showWhoisError(message) {
        if (!whoisErrorMessage) return;
        whoisErrorMessage.textContent = message;
        whoisErrorMessage.classList.add('visible');
    }

    function formatWhoisResult(data) {
        if (!whoisResultContent) return;
        whoisResultContent.innerHTML = ''; // 이전 결과 초기화
        const list = document.createElement('ul');

        const keyMap = {
            domain_name: '도메인 이름',
            registrar: '등록 기관',
            creation_date: '생성일',
            expiration_date: '만료일',
            updated_date: '최근 업데이트',
            name_servers: '네임서버',
            status: '상태',
            emails: '관리자 이메일',
        };
        
        for (const key in keyMap) {
            if (data[key]) {
                const li = document.createElement('li');
                const strong = document.createElement('strong');
                strong.textContent = keyMap[key] + ':';
                
                const span = document.createElement('span');
                let value = data[key];
                if (Array.isArray(value)) {
                    value = value.join(', ');
                }
                span.textContent = value;

                li.appendChild(strong);
                li.appendChild(span);
                list.appendChild(li);
            }
        }

        if (list.children.length === 0) {
            whoisResultContent.innerHTML = "<span>표시할 정보가 없습니다.</span>";
        } else {
            whoisResultContent.appendChild(list);
        }
    }

    async function runWhoisLookup(domain) {
        if (!whoisResultContent || !whoisResultCard) return;
        
        whoisResultContent.innerHTML = '<div style="text-align:center;"><i class="fas fa-spinner fa-spin"></i> Whois 정보 조회 중...</div>';
        whoisResultCard.style.display = 'block';

        try {
            const response = await fetch(`/api/whois/${domain}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Whois 조회 서버 오류: ${response.status}`);
            }
            
            formatWhoisResult(data);
        } catch (error) {
            showWhoisError(error.message);
            whoisResultCard.style.display = 'none';
            throw error; 
        }
    }
    
    // ===============================================
    //         Port Scan (Real-time)
    // ===============================================
    function setPortScanButtonState(scanning) {
        if (!portScanBtn) return;
        portScanBtn.disabled = scanning;
        portScanBtn.innerHTML = scanning ?
            '<i class="fas fa-spinner fa-spin"></i> 스캔 중... <span id="scanProgress"></span>' :
            '<i class="fas fa-crosshairs"></i> 스캔 시작';
    }

    function showPortScanError(message) {
        if (!portScanErrorMessage) return;
        portScanErrorMessage.textContent = message;
        portScanErrorMessage.classList.add('visible');
    }
    
    // 포트 필터링 로직
    function applyPortFilter(filter) {
        const portItems = document.querySelectorAll('.port-scan-grid > div');
        portItems.forEach(item => {
            const status = item.dataset.status;
            if (filter === 'all' || status === filter) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });

        // 필터 버튼 활성 상태 업데이트
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
    }

    // 실시간으로 포트 스캔 결과를 업데이트하는 함수
    function updatePortResult(data) {
        let portDiv = document.getElementById(`port-${data.port}`);
        if (!portDiv) return; // 미리 생성된 div가 없으면 아무것도 하지 않음

        const status = data.error ? 'error' : data.status.toLowerCase();
        const statusClass = `port-status-${status}`;
        
        // 데이터 속성과 클래스 업데이트
        portDiv.dataset.status = status;
        portDiv.className = ''; // 기존 클래스 초기화
        
        portDiv.innerHTML = `<span>Port ${data.port}:</span> <span class="${statusClass}">${data.status}</span>`;

        if (data.progress) {
            const progressSpan = document.getElementById('scanProgress');
            if (progressSpan) {
                progressSpan.textContent = `(${data.progress.percentage}%)`;
            }
        }
    }
    
    // 스캔 시작 시 포트 그리드를 미리 생성하는 함수
    function setupPortGrid(ports, host, ip, total) {
        if (!portScanResultContent) return;
        
        portScanResultContent.innerHTML = `
            <div style="margin-bottom: 1rem;">
                <strong>호스트:</strong> ${host} (${ip})<br>
                <strong>총 포트 수:</strong> ${total}
            </div>
            <div class="filter-controls">
                <button class="filter-btn active" data-filter="all">전체</button>
                <button class="filter-btn" data-filter="open">열림</button>
                <button class="filter-btn" data-filter="closed">닫힘</button>
            </div>
            <div id="portScanGrid" class="port-scan-grid"></div>
        `;

        const grid = document.getElementById('portScanGrid');
        if (!grid) return;
        
        ports.forEach(port => {
            const portDiv = document.createElement('div');
            portDiv.id = `port-${port}`;
            portDiv.dataset.status = 'loading'; // 초기 상태
            portDiv.innerHTML = `<span>Port ${port}:</span> <span class="port-status-loading">스캔 중...</span>`;
            grid.appendChild(portDiv);
        });
        
        // 필터 버튼에 이벤트 리스너 추가
        const filterControls = document.querySelector('.filter-controls');
        if (filterControls) {
            filterControls.addEventListener('click', (e) => {
                if (e.target.classList.contains('filter-btn')) {
                    applyPortFilter(e.target.dataset.filter);
                }
            });
        }
    }

    function parsePortRange(portString) {
        const ports = [];
        const parts = portString.split(',');
        
        for (const part of parts) {
            const trimmed = part.trim();
            if (trimmed.includes('-')) {
                const [start, end] = trimmed.split('-').map(p => parseInt(p.trim()));
                if (!isNaN(start) && !isNaN(end)) {
                    const rangeStart = Math.min(start, end);
                    const rangeEnd = Math.max(start, end);
                    if (rangeEnd - rangeStart > 2000) {
                        showPortScanError(`포트 범위 ${rangeStart}-${rangeEnd}가 너무 큽니다. 최대 2000개까지 가능합니다.`);
                        return null;
                    }
                    for (let i = rangeStart; i <= rangeEnd; i++) {
                        if (i >= 1 && i <= 65535) ports.push(i);
                    }
                }
            } else {
                const port = parseInt(trimmed);
                if (!isNaN(port) && port >= 1 && port <= 65535) ports.push(port);
            }
        }
        
        const uniquePorts = [...new Set(ports)];
        if (uniquePorts.length > 2000) {
            showPortScanError('한 번에 스캔할 수 있는 최대 포트 수는 2000개입니다.');
            return null;
        }
        return uniquePorts.sort((a, b) => a - b);
    }

    // 수정된 포트 스캔 함수 - CSRF 토큰과 FormData 사용
    async function runPortScanRealtime(host, ports) {
        if (!portScanResultCard || !portScanResultContent) return;
        
        if (eventSource) eventSource.close();
        
        portScanResultCard.style.display = 'block';
        portScanResultContent.innerHTML = '<div style="text-align:center; margin-bottom: 1rem;"><i class="fas fa-spinner fa-spin"></i> 포트 스캔을 시작합니다...</div>';
        
        // CSRF 토큰 가져오기 함수
        function getCSRFToken() {
            // 1. Meta 태그에서 가져오기 (가장 권장되는 방법)
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) return metaToken.getAttribute('content');
            
            // 2. 쿠키에서 가져오기 (백업 방법)
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrf_token') return decodeURIComponent(value);
            }
            
            console.warn('CSRF 토큰을 찾을 수 없습니다');
            return null;
        }
        
        try {
            // FormData를 사용하여 서버가 기대하는 형식으로 데이터 전송
            const formData = new FormData();
            formData.append('host', host);
            formData.append('ports', JSON.stringify(ports));
            
            // CSRF 토큰이 있으면 추가
            const csrfToken = getCSRFToken();
            if (csrfToken) {
                formData.append('csrf_token', csrfToken);
            }
            
            const response = await fetch('/start_portscan', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin', // 쿠키를 포함하여 전송
                headers: {
                    'Accept': 'text/event-stream',
                    // FormData 사용 시 Content-Type은 브라우저가 자동으로 설정합니다
                }
            });
            
            // 응답 타입 확인
            const contentType = response.headers.get('content-type');
            
            // 에러 응답 처리
            if (!response.ok) {
                let errorMessage;
                try {
                    if (contentType && contentType.includes('application/json')) {
                        const error = await response.json();
                        errorMessage = error.error || `포트 스캔 시작 실패 (${response.status})`;
                    } else {
                        const text = await response.text();
                        console.error('서버 응답 (처음 500자):', text.substring(0, 500));
                        
                        // 에러 패턴을 확인하여 사용자에게 친화적인 메시지 제공
                        if (text.includes('CSRF') || text.includes('csrf')) {
                            errorMessage = 'CSRF 토큰 검증 실패. 페이지를 새로고침하고 다시 시도하세요.';
                        } else if (response.status === 404) {
                            errorMessage = '포트 스캔 엔드포인트를 찾을 수 없습니다. 서버 설정을 확인하세요.';
                        } else if (response.status === 405) {
                            errorMessage = '잘못된 요청 방식입니다. POST 메소드가 허용되는지 확인하세요.';
                        } else if (response.status === 400) {
                            errorMessage = '잘못된 요청입니다. 입력값을 확인하세요.';
                        } else {
                            errorMessage = `서버 오류: HTTP ${response.status}`;
                        }
                    }
                } catch (e) {
                    errorMessage = `포트 스캔 시작 실패: ${response.status} (응답 파싱 실패)`;
                }
                throw new Error(errorMessage);
            }
            
            // text/event-stream 응답인지 확인
            if (!contentType || !contentType.includes('text/event-stream')) {
                console.warn('예상한 content-type이 아님:', contentType);
            }
            
            // SSE 스트림 읽기
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.status === 'start') {
                                // 스캔 시작 - 포트 그리드 설정
                                setupPortGrid(ports, data.host, data.ip, data.total);
                            } else if (data.status === 'finished') {
                                // 스캔 완료
                                setPortScanButtonState(false);
                                const progressSpan = document.getElementById('scanProgress');
                                if (progressSpan) progressSpan.parentElement.innerHTML = '<i class="fas fa-check"></i> 완료!';
                            } else if (data.error) {
                                // 서버에서 보낸 에러 메시지
                                showPortScanError(`스캔 중 오류: ${data.error}`);
                            } else if (data.port) {
                                // 개별 포트 결과 업데이트
                                updatePortResult(data);
                            }
                        } catch (e) {
                            console.error('JSON 파싱 오류:', e, "받은 데이터:", line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('포트 스캔 오류:', error);
            showPortScanError(error.message);
            portScanResultCard.style.display = 'none';
            setPortScanButtonState(false);
            throw error;
        }
    }

    async function runStandalonePortScan() {
        if (!portScanHostInput || !portScanPortsInput) return;
        
        const host = portScanHostInput.value.trim();
        const portsInput = portScanPortsInput.value.trim();

        if (!host) {
            showPortScanError("스캔할 호스트 이름을 입력해주세요.");
            return;
        }
        if (!portsInput) {
            portScanErrorMessage.classList.remove('visible');
            portScanResultContent.innerHTML = '<div style="text-align:center; color: var(--text-tertiary);">스캔할 포트가 입력되지 않았습니다.</div>';
            portScanResultCard.style.display = 'block';
            return;
        }
        
        const ports = parsePortRange(portsInput);
        if (!ports) return;

        setPortScanButtonState(true);
        portScanErrorMessage.classList.remove('visible');
        portScanResultCard.style.display = 'none';
        
        try {
            await runPortScanRealtime(host, ports);
        } catch(error) {
            console.error("단독 포트 스캔 실행 오류:", error.message);
            setPortScanButtonState(false);
        }
    }
    
    async function runCombinedDomainScan() {
        if (!whoisDomainInput) return;
        
        const domain = whoisDomainInput.value.trim();
        if (!domain) {
            showWhoisError("조회할 도메인 이름을 입력해주세요.");
            return;
        }

        setWhoisButtonState(true);
        whoisErrorMessage.classList.remove('visible');
        portScanErrorMessage.classList.remove('visible');
        whoisResultCard.style.display = 'none';
        portScanResultCard.style.display = 'none';

        portScanHostInput.value = domain;
        const defaultPorts = '21,22,23,25,53,80,110,143,443,465,587,993,995,3306,3389,5900,8080,8443';
        portScanPortsInput.value = defaultPorts;
        
        const portsToScan = parsePortRange(defaultPorts);

        setPortScanButtonState(true); // 포트 스캔 버튼도 비활성화
        const [whoisResult, portScanResult] = await Promise.allSettled([
            runWhoisLookup(domain),
            portsToScan ? runPortScanRealtime(domain, portsToScan) : Promise.reject(new Error("기본 포트 파싱 실패"))
        ]);
        
        if (whoisResult.status === 'rejected') {
            console.error("Whois 조회 실패:", whoisResult.reason.message);
        }
        if (portScanResult.status === 'rejected') {
            console.error("포트 스캔 실패:", portScanResult.reason.message);
            setPortScanButtonState(false);
        }
        
        setWhoisButtonState(false);
    }

    // ===============================================
    //               초기화 및 이벤트 연결
    // ===============================================
    function initSpeedtest() {
        if (!startTestBtn) return;
        
        startTestBtn.addEventListener('click', async () => {
            setSpeedtestButtonState(true);
            resetSpeedtestUI();
            resultsSection.style.display = 'block';
            testTimestamp.textContent = new Date().toLocaleString('ko-KR', { hour12: false });
            try {
                await getClientIpFromServer();
                await testPing();
                await testDownloadSpeed();
                await testUploadSpeed();
            } catch (error) {
                showSpeedtestError(`테스트 중 오류가 발생했습니다: ${error.message}. 잠시 후 다시 시도해주세요.`);
            } finally {
                setSpeedtestButtonState(false);
            }
        });
    }

    function initWhois() {
        if (!whoisSearchBtn || !whoisDomainInput) return;
        
        whoisSearchBtn.addEventListener('click', runCombinedDomainScan);
        whoisDomainInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') runCombinedDomainScan();
        });
    }

    function initPortScan() {
        if (!portScanBtn || !portScanPortsInput || !portScanHostInput) return;
        
        portScanBtn.addEventListener('click', runStandalonePortScan);
        portScanPortsInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') runStandalonePortScan();
        });
        portScanHostInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') runStandalonePortScan();
        });
    }

    function initEventListeners() {
        // 페이지 언로드 시 이벤트 소스 정리
        window.addEventListener('beforeunload', () => {
            if (eventSource) {
                eventSource.close();
            }
        });
    }

    // 모든 기능 초기화
    function init() {
        document.addEventListener('DOMContentLoaded', () => {
            initSpeedtest();
            initWhois();
            initPortScan();
            initEventListeners();
        });
    }

    // 초기화 실행
    init();
})();