import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.api_integrations import search_amazon, search_flipkart

def run():
    print('Amazon results (sample):')
    for p in search_amazon('iPhone', max_results=2):
        print(p)

    print('\nFlipkart results (sample):')
    for p in search_flipkart('iPhone', max_results=2):
        print(p)

if __name__ == '__main__':
    run()
