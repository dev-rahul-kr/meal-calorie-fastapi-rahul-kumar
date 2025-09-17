def test_register_then_login_with_unregistered_email(client):
    r = client.post("/auth/register", json={
        "first_name":"Rahul","last_name":"T","email":"auth@example.com","password":"pass12345"
    })
    assert r.status_code in (200,201)
    r2 = client.post("/auth/login", json={"email":"auth@example.com","password":"pass12345"})
    assert r2.status_code == 200
    body = r2.json()
    assert "access_token" in body and body["user"]["email"] == "auth@example.com"

def test_register_with_duplicate_email(client):
    client.post("/auth/register", json={
        "first_name":"A","last_name":"B","email":"testduplicate@example.com","password":"pass12345"
    })
    r = client.post("/auth/register", json={
        "first_name":"A","last_name":"B","email":"testduplicate@example.com","password":"pass12345"
    })
    assert r.status_code in (400,409)
