import os
import sys
import csv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask
from models import db, Product


def export_products(db_path='pricepulse.db', out_dir='backups'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_path = os.path.join(out_dir, 'products_147_export.csv')

    with app.app_context():
        products = Product.query.order_by(Product.id).all()
        with open(out_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['Category','Product_Name','Brand','Amazon_Price','Amazon_URL','Flipkart_Price','Flipkart_URL'])
            for p in products:
                writer.writerow([
                    p.category or '',
                    p.product_name or '',
                    p.brand or '',
                    '' if p.amazon_price is None else int(p.amazon_price),
                    p.amazon_url or '',
                    '' if p.flipkart_price is None else int(p.flipkart_price),
                    p.flipkart_url or ''
                ])

    return out_path


if __name__ == '__main__':
    path = export_products()
    print('Exported products to:', path)
