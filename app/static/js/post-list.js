document.addEventListener('DOMContentLoaded', function () {
    // '더보기' 버튼 기능
    const loadMoreButton = document.getElementById('loadMoreButton');
    const postGrid = document.getElementById('postGrid');
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    const loadMoreStatus = document.getElementById('loadMoreStatus');

    if (loadMoreButton && postGrid && loadMoreContainer) {
        loadMoreButton.addEventListener('click', async function () {
            const buttonText = this.querySelector('span');
            const loadUrl = new URL(this.dataset.loadUrl, window.location.origin);
            loadUrl.searchParams.set('page', this.dataset.nextPage);

            this.disabled = true;
            this.setAttribute('aria-busy', 'true');
            buttonText.textContent = '불러오는 중...';
            loadMoreStatus.hidden = true;

            try {
                const response = await fetch(loadUrl, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                if (data.html) {
                    postGrid.insertAdjacentHTML('beforeend', data.html);
                }

                if (data.has_more) {
                    this.dataset.nextPage = String(data.next_page);
                    buttonText.textContent = '더 많은 포스트 보기';
                    this.disabled = false;
                    this.removeAttribute('aria-busy');
                } else {
                    loadMoreContainer.remove();
                }
            } catch (error) {
                buttonText.textContent = '더 많은 포스트 보기';
                this.disabled = false;
                this.removeAttribute('aria-busy');
                loadMoreStatus.textContent = '포스트를 불러오지 못했습니다. 다시 시도해 주세요.';
                loadMoreStatus.hidden = false;
            }
        });
    }

    // 서버 사이드 태그 필터링으로 변경되었으므로 클라이언트 필터링 로직 제거
});
