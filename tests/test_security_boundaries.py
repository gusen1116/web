import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from PIL import Image

from app.routes.gallery import gallery_bp
from app.routes.utils_routes import resolve_public_scan_target, utils_bp
from app.services import gallery_service


def _address_info(*addresses: str):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (address, 0))
        for address in addresses
    ]


class PortScanTargetTests(unittest.TestCase):
    def test_public_address_is_resolved_once_to_numeric_ip(self):
        with patch(
            'app.routes.utils_routes.socket.getaddrinfo',
            return_value=_address_info('93.184.216.34'),
        ) as resolver:
            self.assertEqual(resolve_public_scan_target('example.com'), '93.184.216.34')
            resolver.assert_called_once()

    def test_non_public_addresses_are_rejected(self):
        blocked_addresses = (
            '127.0.0.1',
            '10.0.0.1',
            '169.254.169.254',
            '100.64.0.1',
            '0.0.0.0',
            '224.0.0.1',
        )
        for address in blocked_addresses:
            with self.subTest(address=address), patch(
                'app.routes.utils_routes.socket.getaddrinfo',
                return_value=_address_info(address),
            ):
                with self.assertRaises(ValueError):
                    resolve_public_scan_target(address)

    def test_mixed_public_and_private_dns_answers_are_rejected(self):
        with patch(
            'app.routes.utils_routes.socket.getaddrinfo',
            return_value=_address_info('93.184.216.34', '10.0.0.5'),
        ):
            with self.assertRaises(ValueError):
                resolve_public_scan_target('mixed.example')

    def test_both_scan_endpoints_reject_private_target_before_scanning(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(utils_bp)

        with app.test_client() as client, patch(
            'app.routes.utils_routes.socket.getaddrinfo',
            return_value=_address_info('127.0.0.1'),
        ), patch('app.routes.utils_routes.scan_port') as scanner:
            api_response = client.get('/api/utils/port_scan?host=localhost&ports=80')
            stream_response = client.post(
                '/start_portscan',
                data={'host': 'localhost', 'ports': '[80]'},
            )

        self.assertEqual(api_response.status_code, 400)
        self.assertEqual(stream_response.status_code, 400)
        scanner.assert_not_called()


class GalleryPathTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.static_dir = self.root / 'static'
        self.gallery_dir = self.static_dir / 'gallery_photos'
        self.gallery_dir.mkdir(parents=True)
        self.app = Flask(__name__, static_folder=str(self.static_dir))
        self.app.config.update(TESTING=True, GALLERY_PHOTOS_DIR=str(self.gallery_dir))
        gallery_service._photo_cache = {}

    def tearDown(self):
        gallery_service._photo_cache = {}
        self.temp_dir.cleanup()

    def test_service_rejects_traversal_without_creating_escaped_thumbnail(self):
        outside_image = self.static_dir / 'outside.png'
        Image.new('RGB', (4, 4), 'red').save(outside_image)

        with self.app.test_request_context('/'):
            result = gallery_service.process_photo_file('../outside.png', str(self.gallery_dir))

        self.assertIsNone(result)
        self.assertFalse((self.static_dir / 'outside.jpg').exists())

    def test_service_rejects_symlink_that_escapes_gallery(self):
        outside_image = self.root / 'outside.jpg'
        Image.new('RGB', (4, 4), 'red').save(outside_image)
        (self.gallery_dir / 'linked.jpg').symlink_to(outside_image)

        with self.app.test_request_context('/'):
            result = gallery_service.process_photo_file('linked.jpg', str(self.gallery_dir))

        self.assertIsNone(result)

    def test_valid_gallery_image_and_thumbnail_stay_in_their_roots(self):
        image_path = self.gallery_dir / 'valid.png'
        Image.new('RGB', (4, 4), 'blue').save(image_path)

        with self.app.test_request_context('/'):
            result = gallery_service.process_photo_file('valid.png', str(self.gallery_dir))

        self.assertIsNotNone(result)
        self.assertTrue((self.static_dir / 'gallery_thumbnails' / 'valid.jpg').is_file())

    def test_gallery_route_rejects_encoded_traversal(self):
        self.app.register_blueprint(gallery_bp)
        with self.app.test_client() as client:
            responses = (
                client.get('/gallery/photo/..%2Foutside.jpg'),
                client.get('/gallery/photo/%252e%252e%252foutside.jpg'),
                client.get('/gallery/photo/..%5Coutside.jpg'),
            )

        self.assertTrue(all(response.status_code == 404 for response in responses))


if __name__ == '__main__':
    unittest.main()
