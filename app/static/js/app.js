/**
 * app.js - 통합 JavaScript 파일
 * 모든 기능을 하나의 파일로 통합하여 관리 용이성 개선
 */

document.addEventListener('DOMContentLoaded', function() {
    // 테마 토글 기능
    initThemeToggle();
    
    // 모바일 메뉴 토글
    initMobileMenu();
    
    // 스크롤 시 헤더 숨김/표시 효과
    initScrollHeader();
    
    // 애니메이션 효과
    initAnimations();
    
    // 에디터 초기화 (해당 페이지에 있을 경우)
    if (document.getElementById('editor-container')) {
        initEditor();
    }
    
    // 시뮬레이션 초기화 (해당 페이지에 있을 경우)
    if (document.getElementById('simulationCanvas')) {
        initSimulation();
    }
});

// 테마 토글 기능
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    
    themeToggle.addEventListener('click', function() {
        const isDark = document.documentElement.classList.contains('dark-theme');
        
        if (isDark) {
            document.documentElement.classList.remove('dark-theme');
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
            themeToggle.setAttribute('aria-label', '다크 모드로 전환');
        } else {
            document.documentElement.classList.add('dark-theme');
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
            themeToggle.setAttribute('aria-label', '라이트 모드로 전환');
        }
    });
}

// 모바일 메뉴 토글
function initMobileMenu() {
    const mobileToggle = document.querySelector('.mobile-toggle');
    if (!mobileToggle) return;
    
    mobileToggle.addEventListener('click', function() {
        const mainNav = document.querySelector('.main-nav');
        const headerActions = document.querySelector('.header-actions');
        
        mainNav.classList.toggle('active');
        headerActions.classList.toggle('active');
        
        const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
        mobileToggle.setAttribute('aria-expanded', !isExpanded);
        mobileToggle.setAttribute('aria-label', isExpanded ? '메뉴 열기' : '메뉴 닫기');
        mobileToggle.innerHTML = isExpanded ? '<i class="fas fa-bars"></i>' : '<i class="fas fa-times"></i>';
    });
}

// 스크롤 시 헤더 숨김/표시 효과
function initScrollHeader() {
    let lastScrollTop = 0;
    const scrollThreshold = 50;
    const header = document.querySelector('header');
    
    if (!header) return;
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        
        if (currentScroll > lastScrollTop && currentScroll > scrollThreshold) {
            header.classList.add('hidden');
        } else {
            header.classList.remove('hidden');
        }
        
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    }, { passive: true });
}

// 애니메이션 효과
function initAnimations() {
    const fadeElements = document.querySelectorAll('.fade-in');
    
    if (fadeElements.length === 0) return;
    
    // 관찰자 옵션 설정
    const options = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    // 요소가 보이면 'visible' 클래스 추가
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, options);
    
    // 각 애니메이션 요소 관찰 시작
    fadeElements.forEach((el, index) => {
        el.style.transitionDelay = `${index * 100}ms`;
        observer.observe(el);
    });
}

// 간소화된 에디터 초기화
function initEditor() {
    const contentArea = document.getElementById('content-area');
    const titleInput = document.getElementById('post-title');
    const categorySelect = document.getElementById('post-category');
    const tagsInput = document.getElementById('post-tags');
    const saveButton = document.getElementById('save-post');
    const toolbarButtons = document.querySelectorAll('.toolbar-button');
    const editorContainer = document.getElementById('editor-container');
    
    if (!contentArea || !editorContainer) return;
    
    // 편집 가능하게 설정
    contentArea.contentEditable = 'true';
    contentArea.spellcheck = true;
    
    // 툴바 버튼 이벤트 바인딩
    toolbarButtons.forEach(button => {
        const command = button.dataset.command;
        if (!command) return;
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            switch(command) {
                case 'formatBlock':
                    document.execCommand(command, false, this.dataset.value);
                    break;
                case 'insertImage':
                    handleImageInsertion();
                    break;
                case 'createLink':
                    handleLinkInsertion();
                    break;
                case 'foreColor':
                    applyColorStyle();
                    break;
                case 'hiliteColor':
                    applyBackgroundColor();
                    break;
                case 'insertTable':
                    insertTable();
                    break;
                case 'insertCodeBlock':
                    insertCodeBlock();
                    break;
                case 'resizeImage':
                    resizeSelectedImage();
                    break;
                default:
                    document.execCommand(command, false, null);
                    break;
            }
            
            // 포커스 되돌리기
            contentArea.focus();
        });
    });
    
    // 이미지 삽입 처리
    function handleImageInsertion() {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.click();
        
        fileInput.addEventListener('change', function() {
            if (fileInput.files && fileInput.files[0]) {
                uploadImage(fileInput.files[0]);
            }
        });
    }
    
    // 이미지 업로드
    function uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        // 진행 표시기
        const progressIndicator = document.createElement('div');
        progressIndicator.className = 'upload-progress';
        progressIndicator.innerHTML = '<span>이미지 업로드 중...</span>';
        document.body.appendChild(progressIndicator);
        
        // CSRF 토큰 가져오기
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        // 서버에 업로드
        fetch('/blog/upload', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            progressIndicator.remove();
            
            if (data.success === 1) {
                // 이미지 삽입
                const imgHtml = `<img src="${data.file.url}" alt="업로드된 이미지" class="editor-image">`;
                document.execCommand('insertHTML', false, imgHtml);
            } else {
                alert('이미지 업로드 실패: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            progressIndicator.remove();
            console.error('업로드 오류:', error);
            alert('이미지 업로드 중 오류가 발생했습니다.');
        });
    }
    
    // 링크 삽입 처리
    function handleLinkInsertion() {
        const selection = window.getSelection();
        const selectedText = selection.toString();
        
        // 링크 URL 입력 받기
        const url = prompt('링크 URL을 입력하세요:', 'https://');
        
        if (url && url !== 'https://') {
            if (selectedText) {
                // 선택한 텍스트에 링크 적용
                document.execCommand('createLink', false, url);
                
                // 새 창에서 열리도록 타겟 속성 추가
                const links = contentArea.querySelectorAll('a[href="' + url + '"]');
                links.forEach(link => {
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                });
            } else {
                // 선택한 텍스트가 없으면 새 링크 텍스트 입력 받기
                const linkText = prompt('링크 텍스트를 입력하세요:', '');
                if (linkText) {
                    const linkHtml = `<a href="${url}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
                    document.execCommand('insertHTML', false, linkHtml);
                }
            }
        }
    }
    
    // 색상 적용
    function applyColorStyle() {
        const color = prompt('색상 코드를 입력하세요 (예: #FF0000 또는 red):', '');
        if (color) {
            document.execCommand('foreColor', false, color);
        }
    }
    
    // 배경색 적용
    function applyBackgroundColor() {
        const color = prompt('배경색 코드를 입력하세요 (예: #FFFF00 또는 yellow):', '');
        if (color) {
            document.execCommand('hiliteColor', false, color);
        }
    }
    
    // 테이블 삽입
    function insertTable() {
        const rows = prompt('행 수를 입력하세요:', '3');
        const cols = prompt('열 수를 입력하세요:', '3');
        
        if (rows && cols) {
            const numRows = parseInt(rows);
            const numCols = parseInt(cols);
            
            if (numRows > 0 && numCols > 0) {
                let tableHTML = '<table class="editor-table"><tbody>';
                
                // 헤더 행 생성
                tableHTML += '<tr>';
                for (let j = 0; j < numCols; j++) {
                    tableHTML += `<th>헤더 ${j+1}</th>`;
                }
                tableHTML += '</tr>';
                
                // 데이터 행 생성
                for (let i = 0; i < numRows - 1; i++) {
                    tableHTML += '<tr>';
                    for (let j = 0; j < numCols; j++) {
                        tableHTML += `<td>셀 ${i+1}-${j+1}</td>`;
                    }
                    tableHTML += '</tr>';
                }
                
                tableHTML += '</tbody></table>';
                
                document.execCommand('insertHTML', false, tableHTML);
            }
        }
    }
    
    // 코드 블록 삽입
    function insertCodeBlock() {
        const language = prompt('프로그래밍 언어를 입력하세요 (예: javascript, python):', 'javascript');
        
        if (language) {
            const codeBlockHTML = `<pre><code class="language-${language}">여기에 코드를 입력하세요</code></pre>`;
            document.execCommand('insertHTML', false, codeBlockHTML);
        }
    }
    
    // 이미지 크기 조절
    function resizeSelectedImage() {
        const selectedImage = contentArea.querySelector('img.selected');
        if (!selectedImage) {
            alert('먼저 이미지를 선택해주세요.');
            return;
        }
        
        const width = prompt('너비를 입력하세요 (픽셀):', selectedImage.width);
        if (width) {
            selectedImage.style.width = width + 'px';
        }
    }
    
    // 이미지 선택 이벤트
    contentArea.addEventListener('click', function(e) {
        if (e.target.tagName === 'IMG') {
            // 이미 선택된 이미지 클래스 제거
            const allImages = this.querySelectorAll('img');
            allImages.forEach(img => img.classList.remove('selected'));
            
            // 클릭한 이미지 선택 표시
            e.target.classList.add('selected');
        }
    });
    
    // 저장 버튼 이벤트
    if (saveButton) {
        saveButton.addEventListener('click', savePost);
    }
    
    // 포스트 저장 함수
    function savePost() {
        if (!titleInput.value.trim()) {
            alert('제목을 입력해주세요.');
            titleInput.focus();
            return;
        }
        
        // 콘텐츠 객체 생성
        const contentObj = getContentObject();
        
        const postData = {
            title: titleInput.value.trim(),
            content: JSON.stringify(contentObj),
            category: categorySelect ? categorySelect.value : '',
            tags: tagsInput && tagsInput.value ? tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag) : []
        };
        
        // CSRF 토큰 가져오기
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        // 포스트 ID 확인 (신규 또는 수정)
        const postId = editorContainer.dataset.postId;
        const url = postId ? `/blog/posts/${postId}` : '/blog/posts';
        const method = postId ? 'PUT' : 'POST';
        
        // 저장 진행 표시기
        const saveIndicator = document.createElement('div');
        saveIndicator.className = 'save-indicator';
        saveIndicator.innerHTML = '<span>저장 중...</span>';
        document.body.appendChild(saveIndicator);
        
        // 서버에 저장 요청
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(postData)
        })
        .then(response => response.json())
        .then(data => {
            saveIndicator.remove();
            
            if (data.success) {
                // 성공 페이지로 이동
                window.location.href = postId ? `/blog/post/${postId}` : `/blog/post/${data.id}`;
            } else {
                alert('저장 실패: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            saveIndicator.remove();
            console.error('저장 오류:', error);
            alert('저장 중 오류가 발생했습니다.');
        });
    }
    
    // 에디터 콘텐츠를 구조화된 객체로 변환
    function getContentObject() {
        const blocks = [];
        
        // 자식 노드 처리
        Array.from(contentArea.childNodes).forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                // 텍스트 노드가 공백이 아니면 단락으로 처리
                if (node.textContent.trim()) {
                    blocks.push({
                        type: 'paragraph',
                        content: node.textContent
                    });
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                // 요소 노드 처리
                processElementNode(node, blocks);
            }
        });
        
        return {
            blocks: blocks,
            time: new Date().getTime(),
            version: '1.0.0'
        };
    }
    
    // 요소 노드 처리
    function processElementNode(node, blocks) {
        switch (node.nodeName) {
            case 'P':
                blocks.push({
                    type: 'paragraph',
                    content: node.innerHTML
                });
                break;
                
            case 'H1':
            case 'H2':
            case 'H3':
            case 'H4':
            case 'H5':
            case 'H6':
                blocks.push({
                    type: 'header',
                    level: parseInt(node.nodeName.substring(1)),
                    content: node.innerHTML
                });
                break;
                
            case 'BLOCKQUOTE':
                blocks.push({
                    type: 'quote',
                    content: node.innerHTML
                });
                break;
                
            case 'PRE':
                // 코드 블록 처리
                const codeElement = node.querySelector('code');
                if (codeElement) {
                    const language = codeElement.className.replace('language-', '');
                    blocks.push({
                        type: 'code',
                        content: codeElement.textContent,
                        language: language || 'plaintext'
                    });
                } else {
                    blocks.push({
                        type: 'code',
                        content: node.textContent,
                        language: 'plaintext'
                    });
                }
                break;
                
            case 'UL':
                blocks.push({
                    type: 'list',
                    style: 'unordered',
                    items: Array.from(node.querySelectorAll('li')).map(li => li.innerHTML)
                });
                break;
                
            case 'OL':
                blocks.push({
                    type: 'list',
                    style: 'ordered',
                    items: Array.from(node.querySelectorAll('li')).map(li => li.innerHTML)
                });
                break;
                
            case 'IMG':
                blocks.push({
                    type: 'image',
                    url: node.src,
                    alt: node.alt || '',
                    width: node.style.width || '',
                    height: node.style.height || ''
                });
                break;
                
            case 'HR':
                blocks.push({
                    type: 'delimiter'
                });
                break;
                
            case 'TABLE':
                const rows = [];
                node.querySelectorAll('tr').forEach(tr => {
                    const cells = Array.from(tr.querySelectorAll('td, th')).map(cell => {
                        return {
                            content: cell.innerHTML,
                            isHeader: cell.nodeName === 'TH'
                        };
                    });
                    rows.push(cells);
                });
                blocks.push({
                    type: 'table',
                    rows: rows
                });
                break;
                
            default:
                // 인라인 요소나 기타 요소는 자식 노드 처리
                if (node.childNodes.length > 0) {
                    Array.from(node.childNodes).forEach(childNode => {
                        if (childNode.nodeType === Node.ELEMENT_NODE) {
                            processElementNode(childNode, blocks);
                        } else if (childNode.nodeType === Node.TEXT_NODE && childNode.textContent.trim()) {
                            blocks.push({
                                type: 'paragraph',
                                content: childNode.textContent
                            });
                        }
                    });
                }
                break;
        }
    }
    
    // 기존 콘텐츠 로드
    loadExistingContent();
    
    // 기존 콘텐츠 로드 함수
    function loadExistingContent() {
        const existingContent = document.getElementById('existing-content');
        if (existingContent && existingContent.textContent.trim()) {
            try {
                const contentObj = JSON.parse(existingContent.textContent);
                renderContent(contentObj);
            } catch (e) {
                console.error('콘텐츠 파싱 오류:', e);
                contentArea.innerHTML = existingContent.textContent;
            }
        }
    }
    
    // 콘텐츠 렌더링 함수
    function renderContent(contentObj) {
        if (!contentObj || !contentObj.blocks) return;
        
        let html = '';
        
        contentObj.blocks.forEach(block => {
            switch (block.type) {
                case 'paragraph':
                    html += `<p>${block.content}</p>`;
                    break;
                    
                case 'header':
                    const level = Math.min(Math.max(block.level, 1), 6);
                    html += `<h${level}>${block.content}</h${level}>`;
                    break;
                    
                case 'quote':
                    html += `<blockquote>${block.content}</blockquote>`;
                    break;
                    
                case 'code':
                    const language = block.language || 'plaintext';
                    html += `<pre><code class="language-${language}">${escapeHTML(block.content)}</code></pre>`;
                    break;
                    
                case 'list':
                    const listTag = block.style === 'ordered' ? 'ol' : 'ul';
                    html += `<${listTag}>`;
                    block.items.forEach(item => {
                        html += `<li>${item}</li>`;
                    });
                    html += `</${listTag}>`;
                    break;
                    
                case 'image':
                    html += `<img src="${block.url}" alt="${block.alt || ''}" class="editor-image"`;
                    if (block.width) html += ` style="width:${block.width}"`;
                    if (block.height) html += ` style="height:${block.height}"`;
                    html += '>';
                    break;
                    
                case 'delimiter':
                    html += '<hr>';
                    break;
                    
                case 'table':
                    html += '<table class="editor-table"><tbody>';
                    if (block.rows && block.rows.length > 0) {
                        block.rows.forEach(row => {
                            html += '<tr>';
                            if (row && row.length > 0) {
                                row.forEach(cell => {
                                    const cellTag = cell.isHeader ? 'th' : 'td';
                                    html += `<${cellTag}>${cell.content}</${cellTag}>`;
                                });
                            }
                            html += '</tr>';
                        });
                    }
                    html += '</tbody></table>';
                    break;
                    
                default:
                    console.warn('지원하지 않는 블록 유형:', block.type);
                    break;
            }
        });
        
        contentArea.innerHTML = html;
    }
    
    // HTML 이스케이프 함수
    function escapeHTML(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// 간소화된 시뮬레이션 초기화
function initSimulation() {
    const canvas = document.getElementById('simulationCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 캔버스 크기 설정
    function resizeCanvas() {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // 시뮬레이션 객체 및 설정
    const simulation = {
        particles: [],
        gravity: 9.8,
        friction: 0.01,
        running: false
    };
    
    // 시뮬레이션 초기화
    function initSimulationState() {
        // 초기 입자 생성
        simulation.particles = [];
        for (let i = 0; i < 20; i++) {
            simulation.particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: Math.random() * 2 - 1,
                vy: Math.random() * 2 - 1,
                radius: 5 + Math.random() * 10
            });
        }
    }
    
    // 물리 법칙 적용 및 렌더링
    function updateSimulation() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        for (const particle of simulation.particles) {
            // 물리 법칙 적용
            particle.vy += simulation.gravity * 0.01;
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // 벽 충돌 처리
            if (particle.x < particle.radius) {
                particle.x = particle.radius;
                particle.vx *= -0.8;
            }
            if (particle.x > canvas.width - particle.radius) {
                particle.x = canvas.width - particle.radius;
                particle.vx *= -0.8;
            }
            if (particle.y < particle.radius) {
                particle.y = particle.radius;
                particle.vy *= -0.8;
            }
            if (particle.y > canvas.height - particle.radius) {
                particle.y = canvas.height - particle.radius;
                particle.vy *= -0.8;
            }
            
            // 입자 그리기
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            ctx.fillStyle = '#0366d6';
            ctx.fill();
        }
        
        if (simulation.running) {
            requestAnimationFrame(updateSimulation);
        }
    }
    
    // 시뮬레이션 제어 버튼
    const startButton = document.getElementById('startSimulation');
    const stopButton = document.getElementById('stopSimulation');
    const resetButton = document.getElementById('resetSimulation');
    
    if (startButton) {
        startButton.addEventListener('click', function() {
            simulation.running = true;
            updateSimulation();
        });
    }
    
    if (stopButton) {
        stopButton.addEventListener('click', function() {
            simulation.running = false;
        });
    }
    
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            initSimulationState();
            if (!simulation.running) {
                updateSimulation();
            }
        });
    }
    
    // 매개변수 조정
    const gravityControl = document.getElementById('gravityControl');
    if (gravityControl) {
        gravityControl.addEventListener('input', function(e) {
            simulation.gravity = parseFloat(e.target.value);
            document.getElementById('gravityValue').textContent = e.target.value;
        });
    }
    
    const frictionControl = document.getElementById('frictionControl');
    if (frictionControl) {
        frictionControl.addEventListener('input', function(e) {
            simulation.friction = parseFloat(e.target.value);
            document.getElementById('frictionValue').textContent = e.target.value;
        });
    }
    
    // 시뮬레이션 초기화 및 시작
    initSimulationState();
    updateSimulation();
}