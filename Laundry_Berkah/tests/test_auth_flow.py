def test_app_initializes_and_login_route_is_available(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_login_redirects_to_dashboard(client):
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers.get("Location") == "/dashboard/"
