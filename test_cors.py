import urllib.request
import urllib.error

req = urllib.request.Request('http://127.0.0.1:8000/api/timeseries?query=', headers={'Origin': 'http://localhost:3000'})
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print("HEADERS:")
    print(e.headers)
except Exception as e:
    print("FATAL ERROR:", e)
