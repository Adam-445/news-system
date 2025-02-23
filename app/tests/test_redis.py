def test_redis_set_get(redis_client):
    redis_client.set('key', 'value')
    assert redis_client.get('key') == b'value'