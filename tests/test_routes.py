import pytest
from app import create_app

@pytest.fixture
def test_client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()

def test_dashboard_route(test_client):
    response = test_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Camera Monitor Dashboard" in response.data

def test_manage_route(test_client):
    response = test_client.get("/manage")
    assert response.status_code == 200
    assert b"Manage Cameras" in response.data