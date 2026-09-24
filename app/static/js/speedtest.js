/**
 * Browser-to-speed-server network test.
 * Every measurement request is sent directly from the user's browser to
 * https://api.wagusen.com. The website server is not used as a measurement proxy.
 */
(function () {
    'use strict';

    const app = document.getElementById('speedTestApp');
    if (!app) return;

    const API_BASE = 'https://api.wagusen.com/api/v1';
    const DEFAULT_PORTS = '21,22,25,53,80,443,3306,8080';
    const profiles = {
        small: { warmupMb: 1, downloadMb: 10, uploadMb: 5, attempts: 2 },
        normal: { warmupMb: 2, downloadMb: 25, uploadMb: 10, attempts: 2 },
        large: { warmupMb: 5, downloadMb: 75, uploadMb: 25, attempts: 2 }
    };

    const elements = {
        start: document.getElementById('startSpeedTest'),
        profile: document.getElementById('speedProfile'),
        message: document.getElementById('speedMessage'),
        ping: document.getElementById('pingResult'),
        download: document.getElementById('downloadResult'),
        upload: document.getElementById('uploadResult'),
        progress: document.querySelector('.speed-progress'),
        progressBar: document.getElementById('speedProgressBar')
    };

    const networkTools = {
        dns: {
            form: document.getElementById('dnsLookupForm'),
            input: document.getElementById('dnsDomain'),
            button: document.getElementById('dnsLookupButton'),
            result: document.getElementById('dnsLookupResult')
        },
        port: {
            form: document.getElementById('portScanForm'),
            target: document.getElementById('portScanTarget'),
            ports: document.getElementById('portScanPorts'),
            button: document.getElementById('portScanButton'),
            result: document.getElementById('portScanResult')
        },
        subdomain: {
            form: document.getElementById('subdomainLookupForm'),
            input: document.getElementById('subdomainDomain'),
            button: document.getElementById('subdomainLookupButton'),
            result: document.getElementById('subdomainLookupResult')
        }
    };

    let activeController = null;
    let running = false;

    function endpoint(path) {
        return `${API_BASE}${path}`;
    }

    function cacheBuster(index = 0) {
        return `${Date.now()}-${index}-${Math.random().toString(36).slice(2)}`;
    }

    async function apiRequest(path, options = {}) {
        const controller = new AbortController();
        let timedOut = false;
        const timeout = window.setTimeout(() => {
            timedOut = true;
            controller.abort();
        }, 15000);

        try {
            const response = await fetch(endpoint(path), {
                ...options,
                signal: controller.signal
            });

            const responseBody = await response.text();
            let data = {};
            try {
                data = responseBody ? JSON.parse(responseBody) : {};
            } catch (error) {
                if (!response.ok) throw new Error(`API 오류: ${response.status}`);
                throw new Error('API 응답 형식이 올바르지 않습니다.');
            }

            if (!response.ok) {
                throw new Error(data.message || data.error || `API 오류: ${response.status}`);
            }
            return data;
        } catch (error) {
            if (timedOut) throw new Error('요청 시간이 초과되었습니다.');
            if (error instanceof TypeError) throw new Error('API에 연결하지 못했습니다.');
            throw error;
        } finally {
            window.clearTimeout(timeout);
        }
    }

    function setToolBusy(tool, busy, busyText, idleText) {
        tool.button.disabled = busy;
        tool.button.textContent = busy ? busyText : idleText;
        tool.form.setAttribute('aria-busy', String(busy));
    }

    function showToolMessage(container, message, type = '') {
        container.replaceChildren();
        container.textContent = message;
        container.classList.toggle('error', type === 'error');
        container.hidden = false;
    }

    function prepareToolResult(container) {
        container.replaceChildren();
        container.classList.remove('error');
        container.hidden = false;
    }

    function normalizeDomain(value) {
        const rawValue = value.trim();
        if (!rawValue) throw new Error('도메인을 입력해 주세요.');

        let hostname;
        try {
            const url = new URL(rawValue.includes('://') ? rawValue : `http://${rawValue}`);
            hostname = url.hostname.toLowerCase().replace(/\.$/, '');
        } catch (error) {
            throw new Error('도메인 형식을 확인해 주세요.');
        }

        const labels = hostname.split('.');
        const valid = hostname.length <= 253
            && labels.length >= 2
            && labels.every(label => label.length > 0
                && label.length <= 63
                && /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(label));
        if (!valid) throw new Error('도메인 형식을 확인해 주세요.');
        return hostname;
    }

    function normalizeTarget(value) {
        const rawValue = value.trim();
        if (!rawValue) throw new Error('호스트를 입력해 주세요.');

        let target = rawValue;
        if (rawValue.includes('://')) {
            try {
                target = new URL(rawValue).hostname;
            } catch (error) {
                throw new Error('호스트 형식을 확인해 주세요.');
            }
        }
        if (target.length > 253 || !/^[a-z0-9.:\[\]-]+$/i.test(target)) {
            throw new Error('호스트 형식을 확인해 주세요.');
        }
        return target.toLowerCase().replace(/\.$/, '');
    }

    function normalizePorts(value) {
        const portInput = value.trim() || DEFAULT_PORTS;
        const tokens = portInput
            .replace(/[~～]/g, '-')
            .split(',')
            .map(token => token.trim())
            .filter(Boolean);

        let portCount = 0;
        for (const token of tokens) {
            const match = token.match(/^(\d{1,5})(?:-(\d{1,5}))?$/);
            if (!match) throw new Error('포트는 80,443 또는 1-100 형식으로 입력해 주세요.');
            const start = Number(match[1]);
            const end = Number(match[2] || match[1]);
            if (start < 1 || end > 65535 || start > end) {
                throw new Error('포트 범위는 1부터 65535까지입니다.');
            }
            portCount += end - start + 1;
        }
        if (portCount > 100) throw new Error('포트는 한 번에 100개까지 스캔할 수 있습니다.');
        return tokens.join(',');
    }

    function recordValue(record) {
        if (record === null || record === undefined) return '';
        if (typeof record !== 'object') return String(record);

        const rawValue = record.value ?? record.target ?? record.exchange ?? '';
        const value = Array.isArray(rawValue) ? rawValue.join(' ') : String(rawValue);
        return record.priority === undefined || record.priority === null
            ? value
            : `${record.priority} ${value}`.trim();
    }

    function appendResultList(container, title, values) {
        const group = document.createElement('div');
        group.className = 'result-group';

        const heading = document.createElement('strong');
        heading.className = 'result-group-title';
        heading.textContent = title;
        group.appendChild(heading);

        const list = document.createElement('ul');
        list.className = 'result-list';
        for (const value of values) {
            const item = document.createElement('li');
            item.textContent = value;
            list.appendChild(item);
        }
        group.appendChild(list);
        container.appendChild(group);
    }

    function renderDnsResult(container, data) {
        prepareToolResult(container);
        const records = data && typeof data.records === 'object' && data.records ? data.records : {};
        let hasResult = false;

        for (const type of ['NS', 'A', 'AAAA', 'MX', 'TXT', 'CAA']) {
            const values = Array.isArray(records[type])
                ? records[type].map(recordValue).filter(Boolean)
                : [];
            if (values.length) {
                appendResultList(container, type, values);
                hasResult = true;
            }
        }

        const errors = data && typeof data.errors === 'object' && data.errors ? data.errors : {};
        const errorValues = Object.entries(errors).map(([type, error]) => {
            if (error && typeof error === 'object') {
                return `${type}: ${error.message || error.error || JSON.stringify(error)}`;
            }
            return `${type}: ${String(error)}`;
        });
        if (errorValues.length) {
            appendResultList(container, '오류', errorValues);
            hasResult = true;
        }

        if (!hasResult) showToolMessage(container, '조회된 DNS 레코드가 없습니다.');
    }

    function subdomainValue(item) {
        if (typeof item === 'string') return item;
        if (!item || typeof item !== 'object') return String(item || '');
        return String(item.name ?? item.domain ?? item.hostname ?? '');
    }

    function renderSubdomainResult(container, data) {
        prepareToolResult(container);
        const subdomains = Array.isArray(data.subdomains)
            ? data.subdomains.map(subdomainValue).filter(Boolean)
            : [];
        if (!subdomains.length) {
            showToolMessage(container, '검색된 서브도메인이 없습니다.');
            return;
        }

        const summary = document.createElement('strong');
        summary.className = 'result-summary';
        const total = Number.isFinite(Number(data.total_found)) ? Number(data.total_found) : subdomains.length;
        summary.textContent = `${total}개`;
        container.appendChild(summary);
        appendResultList(container, '서브도메인', subdomains);
    }

    function renderPortResult(container, data) {
        prepareToolResult(container);
        const results = Array.isArray(data.results) ? data.results : [];
        if (!results.length) {
            showToolMessage(container, '포트 스캔 결과가 없습니다.');
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'port-result-grid';
        for (const headingText of ['포트', '서비스', '상태', '지연']) {
            const heading = document.createElement('span');
            heading.className = 'result-table-heading';
            heading.textContent = headingText;
            grid.appendChild(heading);
        }

        for (const result of results) {
            const status = String(result.status || '-');
            const values = [
                String(result.port ?? '-'),
                String(result.service || '-'),
                status,
                result.latency_ms === null || result.latency_ms === undefined ? '-' : `${result.latency_ms} ms`
            ];
            values.forEach((value, index) => {
                const cell = document.createElement('span');
                cell.textContent = value;
                if (index === 2) {
                    cell.className = status.toLowerCase() === 'open' ? 'port-status-open' : 'port-status-closed';
                }
                grid.appendChild(cell);
            });
        }
        container.appendChild(grid);
    }

    function setProgress(value) {
        const progress = Math.max(0, Math.min(100, value));
        elements.progressBar.style.width = `${progress}%`;
        elements.progress.setAttribute('aria-valuenow', String(Math.round(progress)));
    }

    function setMessage(text, type = '') {
        elements.message.textContent = text;
        elements.message.classList.toggle('error', type === 'error');
        elements.message.classList.toggle('success', type === 'success');
    }

    function calculateMbps(bytes, elapsedMs) {
        if (!Number.isFinite(bytes) || bytes <= 0 || elapsedMs <= 0) return 0;
        return (bytes * 8) / (elapsedMs / 1000) / 1_000_000;
    }

    function delay(ms, signal) {
        return new Promise((resolve, reject) => {
            const timer = window.setTimeout(resolve, ms);
            signal.addEventListener('abort', () => {
                window.clearTimeout(timer);
                reject(new DOMException('측정이 취소되었습니다.', 'AbortError'));
            }, { once: true });
        });
    }

    async function fetchWithTimeout(url, options, timeoutMs) {
        const timeoutController = new AbortController();
        const parentSignal = options.signal;
        const abortFromParent = () => timeoutController.abort(parentSignal.reason);
        if (parentSignal) {
            if (parentSignal.aborted) abortFromParent();
            else parentSignal.addEventListener('abort', abortFromParent, { once: true });
        }

        let timedOut = false;
        const timeout = window.setTimeout(() => {
            timedOut = true;
            timeoutController.abort();
        }, timeoutMs);
        try {
            return await fetch(url, { ...options, signal: timeoutController.signal });
        } catch (error) {
            if (timedOut) throw new Error('측정 서버 응답 시간이 초과되었습니다.');
            throw error;
        } finally {
            window.clearTimeout(timeout);
            if (parentSignal) parentSignal.removeEventListener('abort', abortFromParent);
        }
    }

    async function ensureOk(response, label) {
        if (!response.ok) {
            throw new Error(`${label} API 오류: HTTP ${response.status}`);
        }
        return response;
    }

    async function checkHealth(signal) {
        const response = await fetchWithTimeout(
            endpoint(`/health?t=${cacheBuster()}`),
            { cache: 'no-store', signal },
            8000
        );
        await ensureOk(response, '서버 상태');
        const health = await response.json();
        if (health.status && health.status !== 'ok') {
            throw new Error(`측정 서버 상태가 정상이 아닙니다: ${health.status}`);
        }
        return health;
    }

    async function measurePing(signal, attempts = 7) {
        const samples = [];
        for (let index = 0; index < attempts; index += 1) {
            const startedAt = performance.now();
            const response = await fetchWithTimeout(
                endpoint(`/speedtest/ping?t=${cacheBuster(index)}`),
                { cache: 'no-store', signal },
                5000
            );
            await ensureOk(response, 'Ping');
            await response.json();
            samples.push(performance.now() - startedAt);
            elements.ping.textContent = samples[samples.length - 1].toFixed(1);
            setProgress(5 + ((index + 1) / attempts) * 15);
            if (index < attempts - 1) await delay(100, signal);
        }

        samples.sort((a, b) => a - b);
        const trimmed = samples.length > 2 ? samples.slice(1, -1) : samples;
        return trimmed.reduce((sum, value) => sum + value, 0) / trimmed.length;
    }

    async function downloadSample(sizeMb, signal, onProgress) {
        const expectedBytes = sizeMb * 1024 * 1024;
        const startedAt = performance.now();
        const response = await fetchWithTimeout(
            endpoint(`/speedtest/download?size_mb=${sizeMb}&t=${cacheBuster()}`),
            { cache: 'no-store', signal },
            120000
        );
        await ensureOk(response, '다운로드');

        let receivedBytes = 0;
        if (response.body && response.body.getReader) {
            const reader = response.body.getReader();
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                receivedBytes += value.byteLength;
                onProgress(Math.min(receivedBytes / expectedBytes, 1));
            }
        } else {
            const data = await response.arrayBuffer();
            receivedBytes = data.byteLength;
            onProgress(1);
        }

        return { bytes: receivedBytes, elapsedMs: performance.now() - startedAt };
    }

    function createRandomPayload(sizeMb) {
        const payload = new Uint8Array(sizeMb * 1024 * 1024);
        const cryptoChunkSize = 65536;
        for (let offset = 0; offset < payload.length; offset += cryptoChunkSize) {
            crypto.getRandomValues(payload.subarray(offset, Math.min(offset + cryptoChunkSize, payload.length)));
        }
        return payload;
    }

    async function uploadSample(sizeMb, signal) {
        const payload = createRandomPayload(sizeMb);
        const startedAt = performance.now();
        const response = await fetchWithTimeout(
            endpoint(`/speedtest/upload?t=${cacheBuster()}`),
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/octet-stream' },
                body: payload,
                cache: 'no-store',
                signal
            },
            120000
        );
        await ensureOk(response, '업로드');
        const result = await response.json();
        const receivedBytes = Number(result.received_bytes);
        if (!Number.isFinite(receivedBytes) || receivedBytes <= 0) {
            throw new Error('업로드 API 응답에 received_bytes가 없습니다.');
        }
        return { bytes: receivedBytes, elapsedMs: performance.now() - startedAt };
    }

    function weightedMbps(samples) {
        const totals = samples.reduce((result, sample) => ({
            bytes: result.bytes + sample.bytes,
            elapsedMs: result.elapsedMs + sample.elapsedMs
        }), { bytes: 0, elapsedMs: 0 });
        return calculateMbps(totals.bytes, totals.elapsedMs);
    }

    function friendlyError(error) {
        if (error.name === 'AbortError') return '측정이 취소되었습니다.';
        if (window.location.protocol === 'https:' && API_BASE.startsWith('http:')) {
            return 'HTTPS 페이지에서는 HTTP 측정 서버를 호출할 수 없습니다. API 서버에도 HTTPS를 적용해 주세요.';
        }
        if (error instanceof TypeError) {
            return '측정 서버에 연결하지 못했습니다. 서버 실행 상태, 방화벽과 API_ALLOWED_ORIGINS의 웹사이트 Origin을 확인해 주세요.';
        }
        return error.message || '알 수 없는 측정 오류가 발생했습니다.';
    }

    function resetResults() {
        elements.ping.textContent = '--';
        elements.download.textContent = '--';
        elements.upload.textContent = '--';
        setProgress(0);
    }

    async function runSpeedTest() {
        if (running) {
            activeController.abort();
            return;
        }
        if (!/^https?:\/\//i.test(API_BASE)) {
            setMessage('측정 서버 주소가 올바르지 않습니다.', 'error');
            return;
        }
        if (window.location.protocol === 'https:' && API_BASE.startsWith('http:')) {
            setMessage('HTTPS 페이지에서는 HTTP 측정 서버가 Mixed Content로 차단됩니다.', 'error');
            return;
        }

        running = true;
        activeController = new AbortController();
        const signal = activeController.signal;
        const profile = profiles[elements.profile.value] || profiles.normal;
        elements.profile.disabled = true;
        elements.start.textContent = '측정 취소';
        resetResults();

        try {
            setMessage('측정 서버 연결을 확인하고 있습니다.');
            await checkHealth(signal);
            setProgress(5);

            setMessage('Ping을 7회 측정하고 있습니다.');
            const ping = await measurePing(signal);
            elements.ping.textContent = ping.toFixed(1);

            setMessage('다운로드 워밍업을 진행하고 있습니다.');
            await downloadSample(profile.warmupMb, signal, ratio => setProgress(20 + ratio * 5));

            const downloadSamples = [];
            for (let index = 0; index < profile.attempts; index += 1) {
                setMessage(`다운로드 속도를 측정하고 있습니다. (${index + 1}/${profile.attempts})`);
                const rangeStart = 25 + (index / profile.attempts) * 40;
                const rangeSize = 40 / profile.attempts;
                const sample = await downloadSample(
                    profile.downloadMb,
                    signal,
                    ratio => setProgress(rangeStart + ratio * rangeSize)
                );
                downloadSamples.push(sample);
                elements.download.textContent = weightedMbps(downloadSamples).toFixed(1);
                if (index < profile.attempts - 1) await delay(250, signal);
            }

            const uploadSamples = [];
            for (let index = 0; index < profile.attempts; index += 1) {
                setMessage(`업로드 속도를 측정하고 있습니다. (${index + 1}/${profile.attempts})`);
                const sample = await uploadSample(profile.uploadMb, signal);
                uploadSamples.push(sample);
                elements.upload.textContent = weightedMbps(uploadSamples).toFixed(1);
                setProgress(65 + ((index + 1) / profile.attempts) * 35);
                if (index < profile.attempts - 1) await delay(250, signal);
            }

            setProgress(100);
            setMessage('측정이 완료되었습니다.', 'success');
        } catch (error) {
            const cancelled = signal.aborted;
            setMessage(friendlyError(error), cancelled ? '' : 'error');
            console.error('Speed test failed:', error);
        } finally {
            running = false;
            activeController = null;
            elements.profile.disabled = false;
            elements.start.textContent = '다시 측정';
        }
    }

    async function handleDnsLookup(event) {
        event.preventDefault();
        const tool = networkTools.dns;
        try {
            const domain = normalizeDomain(tool.input.value);
            setToolBusy(tool, true, '조회 중', '조회');
            showToolMessage(tool.result, '조회 중...');
            const params = new URLSearchParams({ domain, types: 'NS,A,AAAA,MX,TXT,CAA' });
            const data = await apiRequest(`/domain/dns?${params.toString()}`);
            renderDnsResult(tool.result, data);
        } catch (error) {
            showToolMessage(tool.result, error.message || '조회하지 못했습니다.', 'error');
        } finally {
            setToolBusy(tool, false, '조회 중', '조회');
        }
    }

    async function handleSubdomainLookup(event) {
        event.preventDefault();
        const tool = networkTools.subdomain;
        try {
            const domain = normalizeDomain(tool.input.value);
            setToolBusy(tool, true, '검색 중', '검색');
            showToolMessage(tool.result, '검색 중...');
            const params = new URLSearchParams({ domain, limit: '100' });
            const data = await apiRequest(`/domain/subdomains?${params.toString()}`);
            renderSubdomainResult(tool.result, data);
        } catch (error) {
            showToolMessage(tool.result, error.message || '검색하지 못했습니다.', 'error');
        } finally {
            setToolBusy(tool, false, '검색 중', '검색');
        }
    }

    async function handlePortScan(event) {
        event.preventDefault();
        const tool = networkTools.port;
        try {
            const target = normalizeTarget(tool.target.value);
            const ports = normalizePorts(tool.ports.value);
            setToolBusy(tool, true, '스캔 중', '스캔');
            showToolMessage(tool.result, '스캔 중...');
            const data = await apiRequest('/network/port-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target, ports, timeout: 1 })
            });
            renderPortResult(tool.result, data);
        } catch (error) {
            showToolMessage(tool.result, error.message || '스캔하지 못했습니다.', 'error');
        } finally {
            setToolBusy(tool, false, '스캔 중', '스캔');
        }
    }

    elements.start.addEventListener('click', runSpeedTest);
    networkTools.dns.form.addEventListener('submit', handleDnsLookup);
    networkTools.port.form.addEventListener('submit', handlePortScan);
    networkTools.subdomain.form.addEventListener('submit', handleSubdomainLookup);
})();
