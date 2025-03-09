// content-manager.js
class ContentManager {
    constructor(contentArea) {
        // EditorCore 참조 대신 필요한 DOM 요소만 전달받음
        this.contentArea = contentArea;
    }
    
    loadExistingContent() {
        // 기존 콘텐츠 로드 로직
        const existingContent = document.getElementById('existing-content');
        if (existingContent && existingContent.textContent.trim() && this.contentArea) {
            try {
                const contentObj = JSON.parse(existingContent.textContent);
                this.renderContent(contentObj);
            } catch (e) {
                console.error('콘텐츠 파싱 오류:', e);
                this.contentArea.innerHTML = existingContent.textContent;
            }
        }
    }
    
    getContentObject() {
        if (!this.contentArea) {
            return { blocks: [], time: new Date().getTime(), version: '1.0.0' };
        }
        
        const blocks = [];
        this.processContentBlocks(this.contentArea.childNodes, blocks);
        
        return {
            blocks: blocks,
            time: new Date().getTime(),
            version: '1.0.0'
        };
    }
    
    processContentBlocks(nodes, blocks) {
        Array.from(nodes).forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                // 텍스트 노드가 공백이 아니면 단락으로 처리
                if (node.textContent.trim()) {
                    blocks.push({
                        type: 'paragraph',
                        content: node.textContent
                    });
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                this.processElementNode(node, blocks);
            }
        });
    }
    
    processElementNode(node, blocks) {
        // 원본 요소의 모든 속성을 보존하기 위한 함수
        const preserveAttributes = (element) => {
            const attributes = {};
            Array.from(element.attributes).forEach(attr => {
                attributes[attr.name] = attr.value;
            });
            return attributes;
        };
        
        switch (node.nodeName) {
            case 'P':
                blocks.push({
                    type: 'paragraph',
                    content: node.innerHTML,
                    attributes: preserveAttributes(node)
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
                    content: node.innerHTML,
                    attributes: preserveAttributes(node)
                });
                break;
                
            case 'BLOCKQUOTE':
                blocks.push({
                    type: 'quote',
                    content: node.innerHTML,
                    attributes: preserveAttributes(node)
                });
                break;
            
            case 'PRE':
                // 코드 블록 처리
                const codeElement = node.querySelector('code');
                if (codeElement) {
                    const language = codeElement.className.replace('language-', '');
                    blocks.push({
                        type: 'code',
                        content: codeElement.innerHTML,
                        language: language || 'plaintext',
                        attributes: preserveAttributes(node)
                    });
                } else {
                    blocks.push({
                        type: 'code',
                        content: node.innerHTML,
                        language: 'plaintext',
                        attributes: preserveAttributes(node)
                    });
                }
                break;

            case 'UL':
                blocks.push({
                    type: 'list',
                    style: 'unordered',
                    items: Array.from(node.querySelectorAll('li')).map(li => li.innerHTML),
                    attributes: preserveAttributes(node)
                });
                break;
                
            case 'OL':
                blocks.push({
                    type: 'list',
                    style: 'ordered',
                    items: Array.from(node.querySelectorAll('li')).map(li => li.innerHTML),
                    attributes: preserveAttributes(node)
                });
                break;
                
            case 'IMG':
                blocks.push({
                    type: 'image',
                    url: node.src,
                    alt: node.alt || '',
                    caption: node.getAttribute('data-caption') || '',
                    attributes: preserveAttributes(node)
                });
                break;
                
            case 'HR':
                blocks.push({
                    type: 'delimiter',
                    attributes: preserveAttributes(node)
                });
                break;
                
            case 'TABLE':
                const rows = [];
                node.querySelectorAll('tr').forEach(tr => {
                    const cells = Array.from(tr.querySelectorAll('td, th')).map(cell => {
                        return {
                            content: cell.innerHTML,
                            isHeader: cell.nodeName === 'TH',
                            attributes: preserveAttributes(cell)
                        };
                    });
                    rows.push(cells);
                });
                blocks.push({
                    type: 'table',
                    rows: rows,
                    attributes: preserveAttributes(node)
                });
                break;
                
            case 'DIV':
                // 미디어 임베드 처리
                if (node.classList.contains('media-embed')) {
                    const embedType = node.classList.contains('youtube-embed') ? 'youtube' :
                                node.classList.contains('twitch-embed') ? 'twitch' :
                                node.classList.contains('twitter-embed') ? 'twitter' : 'unknown';
                
                    let embedData = {};
                    
                    if (embedType === 'youtube') {
                        const iframe = node.querySelector('iframe');
                        if (iframe) {
                            const src = iframe.src;
                            const videoId = src.match(/embed\/([^?]+)/);
                            if (videoId && videoId[1]) {
                                embedData.videoId = videoId[1];
                            }
                        }
                    } else if (embedType === 'twitter') {
                        embedData.tweetId = node.dataset.tweetId;
                    } else if (embedType === 'twitch') {
                        const iframe = node.querySelector('iframe');
                        if (iframe) {
                            const src = iframe.src;
                            const videoId = src.match(/video=(\d+)/);
                            if (videoId && videoId[1]) {
                                embedData.videoId = videoId[1];
                            }
                        }
                    }
                    
                    blocks.push({
                        type: 'embed',
                        service: embedType,
                        data: embedData,
                        html: node.innerHTML,
                        attributes: preserveAttributes(node)
                    });
                } else if (node.classList.contains('file-preview')) {
                    // 파일 첨부 처리
                    const fileData = {
                        url: node.dataset.fileUrl || '',
                        name: node.dataset.fileName || '',
                        type: node.dataset.fileType || '',
                        size: node.dataset.fileSize || ''
                    };
                    
                    blocks.push({
                        type: 'file',
                        data: fileData,
                        html: node.innerHTML,
                        attributes: preserveAttributes(node)
                    });
                } else if (node.classList.contains('iframe-embed-container')) {
                    // iframe 임베드 처리
                    const iframe = node.querySelector('iframe');
                    if (iframe) {
                        blocks.push({
                            type: 'iframe',
                            src: iframe.src,
                            width: iframe.style.width,
                            height: iframe.style.height,
                            html: node.innerHTML,
                            attributes: preserveAttributes(node)
                        });
                    } else {
                        this.processContentBlocks(node.childNodes, blocks);
                    }
                } else {
                    // 일반 div는 내부 노드 처리
                    this.processContentBlocks(node.childNodes, blocks);
                }
                break;
                
            default:
                // 인라인 요소나 기타 요소는 내부 노드 처리
                if (node.childNodes.length > 0) {
                    this.processContentBlocks(node.childNodes, blocks);
                } else if (node.textContent.trim()) {
                    blocks.push({
                        type: 'paragraph',
                        content: node.outerHTML,
                    });
                }
                break;
        }
    }
    
    renderContent(contentObj) {
        if (!contentObj || !contentObj.blocks || !this.contentArea) {
            return;
        }
        
        let html = '';
        
        // 속성 적용 헬퍼 함수
        const applyAttributes = (tag, attributes) => {
            if (!attributes) return tag;
            
            const openingTag = tag.split('>')[0];
            const rest = tag.substring(tag.indexOf('>'));
            
            const attributesString = Object.entries(attributes)
                .map(([key, value]) => `${key}="${value}"`)
                .join(' ');
                
            return `${openingTag} ${attributesString}${rest}`;
        };
        
        contentObj.blocks.forEach(block => {
            switch (block.type) {
                case 'paragraph':
                    let pTag = `<p>${block.content}</p>`;
                    if (block.attributes) {
                        pTag = applyAttributes(pTag, block.attributes);
                    }
                    html += pTag;
                    break;
                    
                case 'header':
                    const level = Math.min(Math.max(block.level, 1), 6);
                    let hTag = `<h${level}>${block.content}</h${level}>`;
                    if (block.attributes) {
                        hTag = applyAttributes(hTag, block.attributes);
                    }
                    html += hTag;
                    break;
                    
                case 'quote':
                    let quoteTag = `<blockquote>${block.content}</blockquote>`;
                    if (block.attributes) {
                        quoteTag = applyAttributes(quoteTag, block.attributes);
                    }
                    html += quoteTag;
                    break;
                    
                case 'code':
                    const language = block.language || 'plaintext';
                    let codeTag = `<pre><code class="language-${language}">${block.content}</code></pre>`;
                    if (block.attributes) {
                        codeTag = applyAttributes(codeTag, block.attributes);
                    }
                    html += codeTag;
                    break;
                    
                case 'list':
                    const listTag = block.style === 'ordered' ? 'ol' : 'ul';
                    let listHtml = `<${listTag}>`;
                    
                    if (block.attributes) {
                        listHtml = applyAttributes(listHtml, block.attributes);
                    }
                    
                    block.items.forEach(item => {
                        listHtml += `<li>${item}</li>`;
                    });
                    
                    listHtml += `</${listTag}>`;
                    html += listHtml;
                    break;
                    
                case 'image':
                    let imgHtml = `<img src="${block.url}" alt="${block.alt || ''}" `;
                    
                    // 추가 속성 처리
                    if (block.attributes) {
                        const attrString = Object.entries(block.attributes)
                            .filter(([key]) => key !== 'src' && key !== 'alt')
                            .map(([key, value]) => `${key}="${value}"`)
                            .join(' ');
                        
                        if (attrString) {
                            imgHtml += `${attrString} `;
                        }
                    }
                    
                    imgHtml += '>';
                    
                    // 캡션 추가
                    if (block.caption) {
                        imgHtml = `<figure>${imgHtml}<figcaption>${block.caption}</figcaption></figure>`;
                    }
                    
                    html += imgHtml;
                    break;
                    
                case 'embed':
                    if (block.html) {
                        html += block.html;
                    } else if (block.service === 'youtube' && block.data?.videoId) {
                        html += `<div class="media-embed youtube-embed">
                            <iframe width="560" height="315" src="https://www.youtube.com/embed/${block.data.videoId}" 
                            frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; 
                            gyroscope; picture-in-picture" allowfullscreen></iframe>
                            <div class="embed-caption">YouTube 동영상</div>
                        </div>`;
                    } else if (block.service === 'twitter' && block.data?.tweetId) {
                        html += `<div class="media-embed twitter-embed" data-tweet-id="${block.data.tweetId}">
                            <blockquote class="twitter-tweet" data-dnt="true">
                                <a href="https://twitter.com/x/status/${block.data.tweetId}"></a>
                            </blockquote>
                            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                            <div class="embed-caption">Twitter 포스트</div>
                        </div>`;
                    } else if (block.service === 'twitch' && block.data?.videoId) {
                        html += `<div class="media-embed twitch-embed">
                            <iframe src="https://player.twitch.tv/?video=${block.data.videoId}&parent=${window.location.hostname}" 
                            frameborder="0" allowfullscreen="true" scrolling="no" height="315" width="560"></iframe>
                            <div class="embed-caption">Twitch 동영상</div>
                        </div>`;
                    }
                    break;
                    
                case 'iframe':
                    if (block.src) {
                        html += `<div class="iframe-embed-container"${block.attributes ? ' ' + Object.entries(block.attributes).map(([k, v]) => `${k}="${v}"`).join(' ') : ''}>
                            <iframe 
                                src="${block.src}" 
                                style="width: ${block.width || '100%'}; height: ${block.height || '400px'}; border: 1px solid #ddd;" 
                                allowfullscreen
                                loading="lazy" 
                                sandbox="allow-scripts allow-same-origin allow-forms">
                            </iframe>
                            <div class="embed-caption" contenteditable="true">iframe 임베드 (더블클릭으로 편집)</div>
                        </div>`;
                    } else if (block.html) {
                        html += block.html;
                    }
                    break;
                    
                case 'file':
                    if (block.data && block.data.url) {
                        html += `<div class="file-preview" data-file-url="${block.data.url}" 
                                data-file-name="${block.data.name}" data-file-type="${block.data.type}" 
                                data-file-size="${block.data.size}">
                            <div class="file-icon"><i class="fas fa-file"></i></div>
                            <div class="file-info">
                                <div class="file-name">${block.data.name}</div>
                                <div class="file-meta">${block.data.type}, ${block.data.size}</div>
                            </div>
                            <a href="${block.data.url}" class="file-download" target="_blank" 
                            download="${block.data.name}">
                                <i class="fas fa-download"></i>
                            </a>
                        </div>`;
                    } else if (block.html) {
                        html += block.html;
                    }
                    break;
                    
                case 'table':
                    let tableHtml = '<table class="editor-table"><tbody>';
                    
                    if (block.attributes) {
                        tableHtml = applyAttributes(tableHtml, block.attributes);
                    }
                    
                    if (block.rows && block.rows.length > 0) {
                        block.rows.forEach(row => {
                            tableHtml += '<tr>';
                            if (row && row.length > 0) {
                                row.forEach(cell => {
                                    const cellTag = cell.isHeader ? 'th' : 'td';
                                    let cellHtml = `<${cellTag}>${cell.content}</${cellTag}>`;
                                    
                                    if (cell.attributes) {
                                        cellHtml = applyAttributes(cellHtml, cell.attributes);
                                    }
                                    
                                    tableHtml += cellHtml;
                                });
                            }
                            tableHtml += '</tr>';
                        });
                    }
                    
                    tableHtml += '</tbody></table>';
                    html += tableHtml;
                    break;
                    
                case 'delimiter':
                    html += '<hr>';
                    break;
                    
                default:
                    console.warn('지원하지 않는 블록 유형:', block.type);
                    break;
            }
        });
        
        this.contentArea.innerHTML = html;
        
        // Twitter 위젯 로딩
        if (this.contentArea.querySelector('.twitter-embed')) {
            if (window.twttr && window.twttr.widgets) {
                window.twttr.widgets.load();
            }
        }
    }

    isInsideCodeBlock(node) {
        while (node && node !== this.contentArea) {
            if (node.nodeName === 'PRE' || node.nodeName === 'CODE') {
                return true;
            }
            node = node.parentNode;
        }
        return false;
    }
    
    getParentBlockElement(node) {
        while (node && node !== this.contentArea) {
            if (node.nodeType === Node.ELEMENT_NODE) {
                const display = window.getComputedStyle(node).display;
                if (display === 'block' || display === 'list-item') {
                    return node;
                }
            }
            node = node.parentNode;
        }
        return null;
    }
}

export default ContentManager;