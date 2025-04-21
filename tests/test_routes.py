import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200