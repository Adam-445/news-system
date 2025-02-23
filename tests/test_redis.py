from fakeredis import FakeRedis
import pytest

@pytest.fixture
def redis_client():
    return FakeRedis()

def test_set_and_get(redis_client):
    redis_client.set('key', 'value')
    assert redis_client.get('key') == b'value'

def test_delete(redis_client):
    redis_client.set('key', 'value')
    redis_client.delete('key')
    assert redis_client.get('key') is None

def test_exists(redis_client):
    redis_client.set('key', 'value')
    assert redis_client.exists('key') is True
    redis_client.delete('key')
    assert redis_client.exists('key') is False