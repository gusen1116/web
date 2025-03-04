// static/js/editor.js
document.addEventListener('DOMContentLoaded', function() {
    const editor = new EditorJS({
        holder: 'editorjs',
        tools: {
            header: {
                class: Header,
                inlineToolbar: ['link']
            },
            paragraph: {
                class: Paragraph,
                inlineToolbar: true
            },
            // 다른 도구들 추가
        },
        data: {}
    });

    // 저장 버튼 이벤트
    document.getElementById('save-post').addEventListener('click', function() {
        editor.save().then((outputData) => {
            savePost(outputData);
        }).catch((error) => {
            console.error('저장 중 오류 발생:', error);
        });
    });

    // 포스트 저장 함수
    function savePost(data) {
        const title = document.getElementById('post-title').value;
        const category = document.getElementById('post-category').value;
        const tags = document.getElementById('post-tags').value.split(',').map(tag => tag.trim());

        fetch('/api/posts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                content: data,
                category: category,
                tags: tags
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = `/posts/${data.id}`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
});