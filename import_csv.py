import csv
import os
from app import create_app
from models import db, Product

def extract_brand(product_name):
    brands = [
        'Samsung', 'Apple', 'OnePlus', 'Xiaomi', 'Redmi', 'POCO', 'Realme', 'iQOO', 'vivo', 
        'Oppo', 'Motorola', 'Moto', 'Nothing', 'CMF', 'Infinix', 'Tecno', 'Honor', 'Google',
        'Pixel', 'Lava', 'HP', 'Dell', 'Lenovo', 'ASUS', 'Acer', 'Microsoft', 'boAt', 
        'Sony', 'JBL', 'Bose', 'Sennheiser'
    ]
    
    for brand in brands:
        if brand.lower() in product_name.lower():
            return brand
    
    return product_name.split()[0] if product_name.split() else 'Unknown'

def import_products_from_csv(csv_file):
    app = create_app()
    
    with app.app_context():
        Product.query.delete()
        db.session.commit()
        
        count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                try:
                    category = row['Category'].strip()
                    product_name = row['Product_Name'].strip()
                    amazon_price = float(row['Amazon_Price'].replace(',', ''))
                    amazon_coupon = row.get('Amazon_Coupon', '').strip()
                    amazon_url = row['Amazon_URL'].strip()
                    flipkart_price = float(row['Flipkart_Price'].replace(',', ''))
                    flipkart_coupon = row.get('Flipkart_Coupon', '').strip()
                    flipkart_url = row['Flipkart_URL'].strip()
                    
                    brand = extract_brand(product_name)
                    
                    product = Product(
                        category=category,
                        product_name=product_name,
                        brand=brand,
                        amazon_price=amazon_price,
                        amazon_coupon=amazon_coupon if amazon_coupon else None,
                        amazon_url=amazon_url,
                        flipkart_price=flipkart_price,
                        flipkart_coupon=flipkart_coupon if flipkart_coupon else None,
                        flipkart_url=flipkart_url
                    )
                    
                    db.session.add(product)
                    count += 1
                    
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
        
        db.session.commit()
        
        print(f"✅ Successfully imported {count} products")
        
        categories = db.session.query(Product.category).distinct().all()
        brands = db.session.query(Product.brand).distinct().all()
        
        print(f"📊 Categories: {[cat[0] for cat in categories]}")
        print(f"🏷️  Total Brands: {len(brands)}")
        
        for category in categories:
            product_count = Product.query.filter_by(category=category[0]).count()
            print(f"   {category[0]}: {product_count} products")

if __name__ == '__main__':
    csv_file = 'attached_assets/Pasted-Category-Product-Name-Amazon-Price-Amazon-URL-Flipkart-Price-Flipkart-URL-Phones-Samsung-Galaxy-M05-1759997348000_1759997348001_1760789852407.txt'
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        exit(1)
    
    print("📥 Importing products from CSV...")
    import_products_from_csv(csv_file)
