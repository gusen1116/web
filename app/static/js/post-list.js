/**
 * 블로그 게시물 목록 JavaScript
 * - 게시물 더 보기/접기 기능
 * - 태그 필터링 기능
 */
(function() {
    'use strict';
    
    // 게시물 더 보기/접기 기능
    function setupToggleMorePosts() {
        const toggleButton = document.getElementById('toggleButton');
        const additionalPosts = document.getElementById('additionalPosts');
        
        if (!toggleButton || !additionalPosts) return;
        
        toggleButton.addEventListener('click', function() {
            additionalPosts.classList.toggle('hidden');
            
            if (additionalPosts.classList.contains('hidden')) {
                toggleButton.innerHTML = '<span>더 많은 포스트 보기</span><i class="fas fa-chevron-down"></i>';
            } else {
                toggleButton.innerHTML = '<span>포스트 접기</span><i class="fas fa-chevron-up"></i>';
            }
        });
    }
    
    // 태그 필터링 기능
    function setupTagFiltering() {
        const tagItems = document.querySelectorAll('.tag-item');
        const postCards = document.querySelectorAll('.post-card-link');
        
        if (!tagItems.length || !postCards.length) return;
        
        let activeTag = null;
        
        tagItems.forEach(tag => {
            tag.addEventListener('click', function() {
                const selectedTag = this.getAttribute('data-tag');
                
                // 이미 활성화된 태그를 다시 클릭한 경우 필터 해제
                if (activeTag === selectedTag) {
                    activeTag = null;
                    tagItems.forEach(t => t.classList.remove('active'));
                    postCards.forEach(post => {
                        post.style.display = '';
                    });
                    return;
                }
                
                // 새 태그 필터 적용
                activeTag = selectedTag;
                
                // 태그 버튼 활성화 상태 업데이트
                tagItems.forEach(t => {
                    t.classList.toggle('active', t.getAttribute('data-tag') === selectedTag);
                });
                
                // 게시물 필터링
                let visibleCount = 0;
                postCards.forEach(post => {
                    const postTags = post.getAttribute('data-tags').split(',');
                    if (postTags.includes(selectedTag)) {
                        post.style.display = '';
                        visibleCount++;
                    } else {
                        post.style.display = 'none';
                    }
                });
                
                // 필터링 시 추가 게시물 영역 자동 펼치기
                const additionalPosts = document.getElementById('additionalPosts');
                const toggleButton = document.getElementById('toggleButton');
                
                if (additionalPosts) {
                    additionalPosts.classList.remove('hidden');
                    
                    if (toggleButton) {
                        toggleButton.innerHTML = '<span>포스트 접기</span><i class="fas fa-chevron-up"></i>';
                    }
                }
            });
        });
    }
    
    // 모든 기능 초기화
    function init() {
        document.addEventListener('DOMContentLoaded', function() {
            setupToggleMorePosts();
            setupTagFiltering();
        });
    }
    
    // 초기화 실행
    init();
})();