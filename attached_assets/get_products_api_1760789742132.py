import json
import urllib.request

urls = [
    'http://127.0.0.1:5000/api/products',
    'http://localhost:5000/api/products',
    'http://10.44.34.245:5000/api/products'
]

for u in urls:
    print('\nRequesting', u)
    try:
        with urllib.request.urlopen(u, timeout=5) as resp:
            body = resp.read().decode('utf-8')
            data = json.loads(body)
            print('  OK —', len(data), 'products')
            for i,item in enumerate(data[:3]):
                print('   ', i+1, item.get('productName') or item.get('productName', item.get('product_name')))
    except Exception as e:
        print('  Error:', e)
