import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app import create_app
from app.services.image_privacy_service import (
    ensure_image_gps_private,
    has_gps_metadata,
    sanitize_image_gps,
)


def _jpeg_with_location_marker(path: Path) -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (24, 16), (20, 80, 140)).save(buffer, format="JPEG")
    jpeg = buffer.getvalue()
    comment = b"GPSLatitude=private-test-value"
    segment = b"\xff\xfe" + (len(comment) + 2).to_bytes(2, "big") + comment
    path.write_bytes(jpeg[:2] + segment + jpeg[2:])


class ImagePrivacyTests(unittest.TestCase):
    def test_sanitizer_removes_location_without_piexif(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "gps.jpg"
            _jpeg_with_location_marker(image_path)

            self.assertTrue(has_gps_metadata(image_path))
            result = sanitize_image_gps(image_path, overwrite=True)

            self.assertTrue(result.gps_removed)
            self.assertFalse(has_gps_metadata(image_path))
            with Image.open(image_path) as image:
                image.verify()

    def test_changed_public_image_is_checked_again(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "photo.jpg"
            Image.new("RGB", (8, 8), "white").save(image_path)
            ensure_image_gps_private(image_path)

            _jpeg_with_location_marker(image_path)
            result = ensure_image_gps_private(image_path)

            self.assertIsNotNone(result)
            self.assertTrue(result.gps_removed)
            self.assertFalse(has_gps_metadata(image_path))

    def test_public_image_routes_sanitize_before_serving(self):
        with tempfile.TemporaryDirectory() as directory:
            static_root = Path(directory) / "static"
            image_dir = static_root / "images" / "posts"
            gallery_dir = static_root / "gallery_photos"
            image_dir.mkdir(parents=True)
            gallery_dir.mkdir(parents=True)

            requests = {
                "/posts/images/upload.jpg": image_dir / "upload.jpg",
                "/static/images/posts/direct.jpg": image_dir / "direct.jpg",
                "/static/gallery_photos/gallery.jpg": gallery_dir / "gallery.jpg",
            }
            for image_path in requests.values():
                _jpeg_with_location_marker(image_path)

            app = create_app("testing")
            app.static_folder = str(static_root)
            with app.test_client() as client:
                for url, image_path in requests.items():
                    with self.subTest(url=url):
                        response = client.get(url)
                        self.assertEqual(response.status_code, 200)
                        response.close()
                        self.assertFalse(has_gps_metadata(image_path))


if __name__ == "__main__":
    unittest.main()
