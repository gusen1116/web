// ContentManager.js
import Utils from './Utils.js';

class ContentManager {
    constructor(contentArea) {
        this.contentArea = contentArea;
    }
    
    loadExistingContent() {
        const existingContent = document.getElementById('existing-content');
        if (existingContent && existingContent.textContent.trim()) {
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
                    caption: node.getAttribute('data-caption') || ''
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
                        html: node.innerHTML
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
                        data: fileData
                    });
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
                        content: node.outerHTML
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
                    html += `<pre><code class="language-${language}">${Utils.escapeHTML(block.content)}</code></pre>`;
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
                    if (block.caption) {
                        html += ` data-caption="${block.caption}"`;
                    }
                    html += '>';
                    
                    if (block.caption) {
                        html += `<figcaption>${block.caption}</figcaption>`;
                    }
                    break;
                    
                case 'embed':
                    switch (block.service) {
                        case 'youtube':
                            if (block.data && block.data.videoId) {
                                html += `<div class="media-embed youtube-embed">
                                    <iframe width="560" height="315" src="https://www.youtube.com/embed/${block.data.videoId}" 
                                    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; 
                                    gyroscope; picture-in-picture" allowfullscreen></iframe>
                                    <div class="embed-caption">YouTube 동영상</div>
                                </div>`;
                            } else {
                                html += block.html || '';
                            }
                            break;
                            
                        case 'twitter':
                            if (block.data && block.data.tweetId) {
                                html += `<div class="media-embed twitter-embed" data-tweet-id="${block.data.tweetId}">
                                    <blockquote class="twitter-tweet" data-dnt="true">
                                        <a href="https://twitter.com/x/status/${block.data.tweetId}"></a>
                                    </blockquote>
                                    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                                    <div class="embed-caption">Twitter 포스트</div>
                                </div>`;
                            } else {
                                html += block.html || '';
                            }
                            break;
                            
                        default:
                            html += block.html || '';
                            break;
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
                                <div class="file-meta">${block.data.type}, ${Utils.formatFileSize(block.data.size)}</div>
                            </div>
                            <a href="${block.data.url}" class="file-download" target="_blank" 
                            download="${block.data.name}">
                                <i class="fas fa-download"></i>
                            </a>
                        </div>`;
                    }
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