from app import create_app

app = create_app('testing')
client = app.test_client()

resp = client.get('/')
print('STATUS', resp.status_code)
print('LOCATION', resp.headers.get('Location'))
print('BODY_PREVIEW')
print(resp.get_data(as_text=True)[:500])
