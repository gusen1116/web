import unittest

from app import create_app


class SpeedtestPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()

    def test_page_exposes_external_api_base_and_csp_origin(self):
        response = self.client.get('/speedtest/')
        html = response.get_data(as_text=True)
        csp = response.headers.get('Content-Security-Policy', '')

        self.assertEqual(response.status_code, 200)
        self.assertIn('https://api.wagusen.com/api/v1', html)
        self.assertIn('https://api.wagusen.com', csp)
        self.assertIn('upgrade-insecure-requests', csp)

    def test_legacy_website_server_measurement_endpoints_are_removed(self):
        self.assertEqual(self.client.get('/speedtest/ping_target').status_code, 404)
        self.assertEqual(self.client.get('/speedtest/download').status_code, 404)
        self.assertEqual(self.client.post('/speedtest/upload').status_code, 404)

    def test_script_calls_only_versioned_measurement_api_paths(self):
        script_path = self.app.static_folder + '/js/speedtest.js'
        with open(script_path, encoding='utf-8') as script_file:
            script = script_file.read()

        self.assertIn("const API_BASE = 'https://api.wagusen.com/api/v1';", script)
        self.assertIn('endpoint(`/health?', script)
        self.assertIn('endpoint(`/speedtest/ping?', script)
        self.assertIn('endpoint(`/speedtest/download?', script)
        self.assertIn('endpoint(`/speedtest/upload?', script)
        self.assertNotIn("fetch('/speedtest/", script)

    def test_network_lookup_tools_use_external_api_and_safe_rendering(self):
        response = self.client.get('/speedtest/')
        html = response.get_data(as_text=True)
        script_path = self.app.static_folder + '/js/speedtest.js'
        with open(script_path, encoding='utf-8') as script_file:
            script = script_file.read()

        for element_id in (
            'dnsLookupForm',
            'dnsLookupResult',
            'portScanForm',
            'portScanResult',
            'subdomainLookupForm',
            'subdomainLookupResult',
        ):
            self.assertIn(f'id="{element_id}"', html)

        self.assertIn('/domain/dns?', script)
        self.assertIn('/domain/subdomains?', script)
        self.assertIn("apiRequest('/network/port-scan'", script)
        self.assertIn("const DEFAULT_PORTS = '21,22,25,53,80,443,3306,8080';", script)
        self.assertIn(".replace(/[~～]/g, '-')", script)
        self.assertIn("headers: { 'Content-Type': 'application/json' }", script)
        self.assertIn('.textContent =', script)
        self.assertNotIn('innerHTML', script)
        self.assertNotIn('X-CSRFToken', script)


if __name__ == '__main__':
    unittest.main()
