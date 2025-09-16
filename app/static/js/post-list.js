document.addEventListener('DOMContentLoaded', function () {
    // '더보기' 버튼 기능
    const toggleButton = document.getElementById('toggleButton');
    const additionalPosts = document.getElementById('additionalPosts');

    if (toggleButton && additionalPosts) {
        toggleButton.addEventListener('click', function () {
            const isHidden = additionalPosts.classList.contains('hidden');
            additionalPosts.classList.toggle('hidden');

            const buttonText = this.querySelector('span');
            const buttonIcon = this.querySelector('i');

            if (isHidden) {
                buttonText.textContent = '접기';
                buttonIcon.classList.remove('fa-chevron-down');
                buttonIcon.classList.add('fa-chevron-up');
            } else {
                buttonText.textContent = '더 많은 포스트 보기';
                buttonIcon.classList.remove('fa-chevron-up');
                buttonIcon.classList.add('fa-chevron-down');
            }
        });
    }

    // 태그 필터링 기능
    const tagContainer = document.querySelector('.top-tag-navigation');
    const postCards = document.querySelectorAll('.post-card-link');
    const emptyState = document.querySelector('.empty-state');

    if (tagContainer && postCards.length > 0) {
        // 'All' 태그가 없는 경우 동적으로 추가
        if (!tagContainer.querySelector('[data-tag="All"]')) {
            const allTag = document.createElement('div');
            allTag.className = 'tag-item active';
            allTag.dataset.tag = 'All';
            allTag.textContent = 'All';
            tagContainer.insertBefore(allTag, tagContainer.firstChild);
        }

        let tagItems = document.querySelectorAll('.tag-item');

        tagItems.forEach(tagItem => {
            tagItem.addEventListener('click', function () {
                const selectedTag = this.dataset.tag;

                // 모든 태그에서 'active' 클래스 제거 후 현재 태그에 추가
                tagItems.forEach(item => item.classList.remove('active'));
                this.classList.add('active');

                let hasVisiblePosts = false;
                postCards.forEach(card => {
                    const postTags = card.dataset.tags.split(',');
                    if (selectedTag === 'All' || postTags.includes(selectedTag)) {
                        card.style.display = 'block';
                        hasVisiblePosts = true;
                    } else {
                        card.style.display = 'none';
                    }
                });

                // 보이는 포스트가 없으면 'empty-state' 메시지 표시
                if (emptyState) {
                    emptyState.style.display = hasVisiblePosts ? 'none' : 'block';
                }
            });
        });
    }
});
