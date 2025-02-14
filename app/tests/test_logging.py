def test_correlation_id_header(client, caplog):
    response = client.get("/api/v1/articles/", headers={"X-Correlation-ID": "test-123"})
    assert response.headers["X-Correlation-ID"] == "test-123"
    
    # Verify logs contain correlation ID
    assert any(
        "correlation_id" in record.message and record.correlation_id == "test-123"
        for record in caplog.records
    )