import urllib.request
for path in ['/auth/login','/dashboard/']:
    try:
        with urllib.request.urlopen('http://127.0.0.1:5000' + path, timeout=5) as resp:
            print(path, resp.status, resp.read(120).decode('utf-8', 'ignore'))
    except Exception as exc:
        print(path, 'ERR', exc)
