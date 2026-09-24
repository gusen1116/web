import unittest

from app import create_app
from app.app_config import TestingConfig
from app.services.text_service import render_content


class MarkdownRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.context = cls.app.app_context()
        cls.context.push()

    @classmethod
    def tearDownClass(cls):
        cls.context.pop()

    def test_fenced_code_keeps_language_and_escapes_markup(self):
        rendered = str(render_content(
            '```python\n'
            'def greet(name):\n'
            '    return f"<b>Hello</b>, {name}"\n'
            '```'
        ))

        self.assertIn('highlight', rendered)
        self.assertIn('&lt;b&gt;Hello&lt;/b&gt;', rendered)
        self.assertNotIn('<b>Hello</b>', rendered)
        self.assertIn('language-python', rendered)

    def test_code_block_never_reactivates_script_markup(self):
        rendered = str(render_content('```html\n<script>alert("xss")</script>\n```'))

        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;', rendered)
        self.assertIn('script', rendered)

    def test_media_embeds_use_styled_semantic_markup(self):
        video = str(render_content('[video:sample.mp4|샘플 영상]'))
        audio = str(render_content('[audio:sample.mp3|샘플 음원]'))

        self.assertIn('class="media-embed video-embed"', video)
        self.assertIn('type="video/mp4"', video)
        self.assertIn('<figcaption>샘플 영상</figcaption>', video)
        self.assertIn('class="media-embed audio-embed"', audio)
        self.assertIn('type="audio/mpeg"', audio)
        self.assertIn('<figcaption>샘플 음원</figcaption>', audio)

    def test_media_elements_are_allowed_by_the_sanitizer_config(self):
        for tag in ('video', 'audio', 'source'):
            self.assertIn(tag, TestingConfig.ALLOWED_HTML_TAGS)

        self.assertIn('controls', TestingConfig.ALLOWED_HTML_ATTRIBUTES['video'])
        self.assertIn('src', TestingConfig.ALLOWED_HTML_ATTRIBUTES['source'])
        self.assertIn('download', TestingConfig.ALLOWED_HTML_ATTRIBUTES['a'])


if __name__ == '__main__':
    unittest.main()
