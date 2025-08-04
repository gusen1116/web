// app/static/js/gallery.js

document.addEventListener('DOMContentLoaded', function() {
    // Tag Filtering Logic
    const tagItems = document.querySelectorAll('.tag-item');
    const photoCards = document.querySelectorAll('.photo-card-link'); // 링크를 직접 제어

    if (tagItems.length > 0 && photoCards.length > 0) {
        tagItems.forEach(tagButton => {
            tagButton.addEventListener('click', function() {
                // 버튼 활성화 상태 관리
                tagItems.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                const selectedTag = this.getAttribute('data-tag');

                // 카드 표시/숨김 처리
                photoCards.forEach(cardLink => {
                    const card = cardLink.querySelector('.photo-card');
                    const photoTags = card.getAttribute('data-tags').split(',');
                    
                    if (selectedTag === 'all' || photoTags.includes(selectedTag)) {
                        cardLink.style.display = 'block';
                    } else {
                        cardLink.style.display = 'none';
                    }
                });
            });
        });
    }
});