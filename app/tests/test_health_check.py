from django.test import TestCase, RequestFactory
from health_check import health_check
import json


class HealthCheckTest(TestCase):
    """ヘルスチェック機能のテストクラス"""
    
    def test_health_check_status_code(self):
        """ヘルスチェックのステータスコードが200であることをテスト"""
        factory = RequestFactory()
        request = factory.get("/health/")
        response = health_check(request)
        self.assertEqual(response.status_code, 200)

    def test_health_check_content(self):
        """ヘルスチェックのレスポンス内容が正しいことをテスト"""
        factory = RequestFactory()
        request = factory.get("/health/")
        response = health_check(request)
        data = json.loads(response.content)
        self.assertEqual(data, {"status": "healthy"})
