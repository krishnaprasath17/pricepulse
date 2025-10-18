import os
import sys
import csv
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask
from models import db, Product, PriceHistory


def parse_price(v):
    if v is None:
        return None
    v = str(v).strip()
    if v == '':
        return None
    try:
        return float(v.replace(',', ''))
    except Exception:
        try:
            return float(v)
        except Exception:
            return None


def force_apply(db_path, file_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # delete existing products and history
        PriceHistory.query.delete()
        Product.query.delete()
        db.session.commit()

        count = 0
        with open(file_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                category = row.get('Category') or row.get('category') or 'Uncategorized'
                product_name = (row.get('Product_Name') or row.get('product_name') or '').strip()
                brand = (row.get('Brand') or row.get('brand') or '').strip()
                amazon_price = parse_price(row.get('Amazon_Price') or row.get('amazon_price')) or 0.0
                amazon_url = (row.get('Amazon_URL') or row.get('amazon_url') or '').strip()
                flipkart_price = parse_price(row.get('Flipkart_Price') or row.get('flipkart_price')) or 0.0
                flipkart_url = (row.get('Flipkart_URL') or row.get('flipkart_url') or '').strip()

                p = Product(category=category, product_name=product_name, brand=brand,
                            amazon_price=amazon_price, amazon_url=amazon_url,
                            flipkart_price=flipkart_price, flipkart_url=flipkart_url)
                db.session.add(p)
                db.session.flush()  # assign id

                # add initial price history pointing to seed
                ph = PriceHistory(product_id=p.id, amazon_price=p.amazon_price, flipkart_price=p.flipkart_price, recorded_at=datetime.utcnow(), source='seed_attachment')
                db.session.add(ph)
                count += 1

        db.session.commit()

    return count


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Force-apply attachment CSV as the only products in the DB')
    parser.add_argument('--file', '-f', required=True, help='Path to CSV file')
    parser.add_argument('--db', default='instance/pricepulse.db', help='Path to sqlite DB file')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print('File not found:', args.file)
        sys.exit(2)

    print('Applying attachment as canonical dataset (destructive)')
    n = force_apply(args.db, args.file)
    print('Inserted products:', n)
