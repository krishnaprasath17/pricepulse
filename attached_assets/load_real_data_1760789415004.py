#!/usr/bin/env python3
"""
Load real product data from CSV into the Flask application
This script will update both the Flask app and create a comprehensive demo
"""

import csv
import json
import re
import argparse
import os

from typing import List, Dict

try:
    from services import api_integrations
except Exception:
    api_integrations = None


def extract_brand(product_name):
    """Extract brand name from product name"""
    brands = [
        'Samsung', 'Apple', 'OnePlus', 'Xiaomi', 'Redmi', 'POCO', 'Realme', 'iQOO', 'vivo', 
        'Oppo', 'Motorola', 'Moto', 'Nothing', 'CMF', 'Infinix', 'Tecno', 'Honor', 'Huawei',
        'HP', 'Dell', 'Lenovo', 'ASUS', 'Acer', 'MSI', 'Microsoft', 'Razer', 'Alienware',
        'Gigabyte', 'Sony', 'JBL', 'Bose', 'Sennheiser', 'Audio-Technica', 'Beyerdynamic',
        'AKG', 'HyperX', 'SteelSeries', 'Logitech', 'Corsair', 'Turtle Beach', 'Astro',
        'Plantronics', 'boAt', 'Noise', 'Mivi', 'Fire-Boltt', 'pTron', 'Boult Audio',
        'Fastrack', 'Zebronics', 'Aroma', 'Caidea', 'TECHFIRE', 'GOBOULT', 'Google', 'Pixel',
        'Lava', 'realme'
    ]
    
    for brand in brands:
        if brand.lower() in product_name.lower():
            return brand
    
    return product_name.split()[0] if product_name.split() else 'Unknown'

def load_products_from_csv():
    """Load products from the CSV file"""
    csv_file = 'attached_assets/Pasted-Category-Product-Name-Amazon-Price-Amazon-URL-Flipkart-Price-Flipkart-URL-Phones-Samsung-Galaxy-M05-1759997348000_1759997348001.txt'
    
    products = []
    categories = set()
    brands = set()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                try:
                    category = row['Category'].strip()
                    product_name = row['Product_Name'].strip()
                    amazon_price = float(row['Amazon_Price'].replace(',', ''))
                    amazon_url = row['Amazon_URL'].strip()
                    flipkart_price = float(row['Flipkart_Price'].replace(',', ''))
                    flipkart_url = row['Flipkart_URL'].strip()
                    
                    brand = extract_brand(product_name)
                    
                    product = {
                        'category': category,
                        'productName': product_name,
                        'brand': brand,
                        'amazonPrice': amazon_price,
                        'amazonUrl': amazon_url,
                        'flipkartPrice': flipkart_price,
                        'flipkartUrl': flipkart_url
                    }
                    
                    products.append(product)
                    categories.add(category)
                    brands.add(brand)
                    
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
        
        print(f"✅ Loaded {len(products)} products")
        print(f"📊 Categories: {sorted(categories)}")
        print(f"🏷️  Brands: {len(brands)} unique brands")
        
        return products, sorted(categories), sorted(brands)
        
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file}")
        return [], [], []
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return [], [], []

def fetch_products_from_apis(queries: List[str], max_per_query: int = 5) -> List[Dict]:
    """Fetch products from official APIs (Amazon and Flipkart) using adapters.
    Returns a list of product dicts shaped like the CSV loader expects.
    """
    if api_integrations is None:
        print('❌ services.api_integrations is not available; cannot fetch from APIs')
        return []

    results = []
    for q in queries:
        try:
            a_items = api_integrations.search_amazon(q, max_results=max_per_query)
        except Exception as e:
            print(f'⚠️ Amazon API error for "{q}": {e}')
            a_items = []

        try:
            f_items = api_integrations.search_flipkart(q, max_results=max_per_query)
        except Exception as e:
            print(f'⚠️ Flipkart API error for "{q}": {e}')
            f_items = []

        # Merge and normalize
        for it in (a_items + f_items):
            try:
                title = it.get('title') or it.get('product_title') or it.get('name')
                price = it.get('price') or it.get('offer_price') or 0
                url = it.get('url') or it.get('detail_page_url') or ''
                platform = it.get('platform', '')

                # Basic brand extraction
                brand = it.get('brand') or it.get('manufacturer') or extract_brand(title or '')

                product = {
                    'category': 'Phones' if any(x in title.lower() for x in ['phone', 'iphone', 'galaxy', 'poco', 'redmi', 'oneplus', 'pixel']) else 'Electronics',
                    'productName': title,
                    'brand': brand,
                    'amazonPrice': price if platform.lower() == 'amazon' else 0,
                    'amazonUrl': url if platform.lower() == 'amazon' else '',
                    'flipkartPrice': price if platform.lower() == 'flipkart' else 0,
                    'flipkartUrl': url if platform.lower() == 'flipkart' else '',
                    # Preserve provenance from adapter/scraper
                    'source': it.get('source') or it.get('platform') and f"{it.get('platform').lower()}_api" or 'api'
                }
                results.append(product)
            except Exception:
                continue

    # dedupe by productName
    seen = set()
    deduped = []
    for p in results:
        name = (p.get('productName') or '').strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        deduped.append(p)

    return deduped
def create_flask_seeder(products=None):
    """Create a Flask seeder script with real data
    If `products` is provided it will be used, otherwise the CSV loader is used.
    """
    if products is None:
        products, categories, brands = load_products_from_csv()
    else:
        categories = sorted({p.get('category', 'Uncategorized') for p in products})
        brands = sorted({p.get('brand', 'Unknown') for p in products})

    if not products:
        print("❌ No products loaded, cannot create seeder")
        return

    seeder_content = f'''#!/usr/bin/env python3
"""
Flask database seeder with real product data
Auto-generated from CSV data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Product

def create_app_for_seeding():
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'seed-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricepulse.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

app = create_app_for_seeding()

# Real product data ({len(products)} products)
REAL_PRODUCTS = {products}

def seed_database():
    """Seed the database with real product data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Clear existing data
        Product.query.delete()
        
        # Add real products
        for product_data in REAL_PRODUCTS:
            product = Product(**product_data)
            db.session.add(product)
        
        # Commit changes
        db.session.commit()
        
        print(f"✅ Successfully seeded database with {{len(REAL_PRODUCTS)}} products")
        
        # Display statistics
        categories = db.session.query(Product.category).distinct().all()
        brands = db.session.query(Product.brand).distinct().all()
        
        print(f"📊 Categories: {{[cat[0] for cat in categories]}}")
        print(f"🏷️  Total Brands: {{len(brands)}}")
        
        # Show product count by category
        for category in categories:
            count = Product.query.filter_by(category=category[0]).count()
            print(f"   {{category[0]}}: {{count}} products")

if __name__ == '__main__':
    seed_database()
'''
    
    with open('seed_real_data.py', 'w', encoding='utf-8') as f:
        f.write(seeder_content)
    
    print("✅ Created seed_real_data.py")

def create_demo_data():
    """Create demo data file for the HTML demo"""
    products, categories, brands = load_products_from_csv()
    
    if not products:
        print("❌ No products loaded, cannot create demo data")
        return
    
    # Select a good mix of products for demo
    demo_products = []
    
    # Select phones
    phone_products = [p for p in products if p['category'] == 'Phones'][:8]
    demo_products.extend(phone_products)
    
    # Select laptops
    laptop_products = [p for p in products if p['category'] == 'Laptops'][:6]
    demo_products.extend(laptop_products)
    
    # Select headphones
    headphone_products = [p for p in products if p['category'] == 'Headphones'][:8]
    demo_products.extend(headphone_products)
    
    # Create JavaScript data
    js_content = f'''        // Real product data from CSV ({len(demo_products)} products for demo)
        const sampleProducts = {json.dumps(demo_products, indent=12)};
'''
    
    print(f"✅ Created demo data with {len(demo_products)} products")
    print(f"   - Phones: {len(phone_products)}")
    print(f"   - Laptops: {len(laptop_products)}")
    print(f"   - Headphones: {len(headphone_products)}")
    
    return js_content


def main_cli():
    parser = argparse.ArgumentParser(description='Load real data from CSV or APIs and generate seeders')
    parser.add_argument('--source', choices=['csv', 'api', 'scraper'], default='csv', help='Data source for seeding')
    parser.add_argument('--queries', nargs='*', help='Search queries to use when source=api')
    parser.add_argument('--max', type=int, default=5, help='Max results per query when using APIs')

    args = parser.parse_args()

    if args.source == 'csv':
        products, categories, brands = load_products_from_csv()
    elif args.source == 'api':
        queries = args.queries or ['iPhone', 'Samsung Galaxy', 'Redmi', 'Dell laptop', 'boAt earbuds']
        products = fetch_products_from_apis(queries, max_per_query=args.max)
        categories = sorted({p.get('category', 'Uncategorized') for p in products})
        brands = sorted({p.get('brand', 'Unknown') for p in products})
    else:
        # scraper path can be added later; for now fall back to CSV
        print('Scraper source not implemented for seeder; falling back to CSV')
        products, categories, brands = load_products_from_csv()

    if not products:
        print('❌ No products obtained from the selected source')
        return

    print(f"\n📊 Data Summary:")
    print(f"   Total Products: {len(products)}")
    print(f"   Categories: {', '.join(categories)}")
    print(f"   Unique Brands: {len(brands)}")

    print(f"\n🔧 Creating Flask seeder...")
    create_flask_seeder(products=products)

    print(f"\n🔧 Updating run_app.py...")
    update_run_app()

    print(f"\n✅ All done! Your Flask app now has real data:")
    print(f"   - {len(products)} products loaded")
    print(f"   - Flask seeder created (seed_real_data.py)")
    print(f"   - run_app.py updated with real data")

    print(f"\n🚀 To run the Flask app with real data:")
    print(f"   python run_app.py")


if __name__ == '__main__':
    main_cli()

def update_run_app():
    """Update run_app.py with real data"""
    products, categories, brands = load_products_from_csv()
    
    if not products:
        print("❌ No products loaded, cannot update run_app.py")
        return
    
    # Read current run_app.py
    with open('run_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the sample products section
    start_marker = 'def seed_sample_data():'
    end_marker = 'def main():'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        # Create new sample data section
        new_sample_data = f'''def seed_sample_data():
    """Seed the database with real product data from CSV"""
    sample_products = {products}
    
    # Clear existing data and add real products
    Product.query.delete()
    for product_data in sample_products:
        product = Product(**product_data)
        db.session.add(product)
    db.session.commit()
    print(f"Seeded database with {{len(sample_products)}} real products")'''
        
        # Replace the section
        new_content = content[:start_idx] + new_sample_data + content[end_idx:]
        
        with open('run_app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Updated run_app.py with real data")

def main():
    print("🔄 Loading real product data from CSV...")
    products, categories, brands = load_products_from_csv()
    
    if products:
        print(f"\\n📊 Data Summary:")
        print(f"   Total Products: {len(products)}")
        print(f"   Categories: {', '.join(categories)}")
        print(f"   Unique Brands: {len(brands)}")
        
        print(f"\\n🔧 Creating Flask seeder...")
        create_flask_seeder()
        
        print(f"\\n🔧 Updating run_app.py...")
        update_run_app()
        
        print(f"\\n🔧 Creating demo data...")
        demo_js = create_demo_data()
        
        print(f"\\n✅ All done! Your Flask app now has real data:")
        print(f"   - {len(products)} products loaded")
        print(f"   - Flask seeder created (seed_real_data.py)")
        print(f"   - run_app.py updated with real data")
        print(f"   - Demo data prepared")
        
        print(f"\\n🚀 To run the Flask app with real data:")
        print(f"   python run_app.py")
        
    else:
        print("❌ Failed to load products from CSV")

if __name__ == '__main__':
    main_cli()
