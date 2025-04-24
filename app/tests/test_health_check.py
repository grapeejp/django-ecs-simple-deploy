import pytest
from django.test import RequestFactory
from health_check import health_check


def test_health_check_status_code():
    factory = RequestFactory()
    request = factory.get('/health/')
    response = health_check(request)
    assert response.status_code == 200


def test_health_check_content():
    factory = RequestFactory()
    request = factory.get('/health/')
    response = health_check(request)
    assert response.json() == {"status": "healthy"} 