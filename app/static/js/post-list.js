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

    // 서버 사이드 태그 필터링으로 변경되었으므로 클라이언트 필터링 로직 제거
});
