#!/usr/bin/env python3
"""Update all product prices using the scraper and record PriceHistory entries.

This script initializes the Flask app (same DB URI as the app), queries all
products from `models.Product`, fetches latest prices via the scraper, and
updates the DB. It also creates `PriceHistory` rows when prices change.
"""
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db, Product, PriceHistory
from scraper import PriceComparisonScraper


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'update-prices'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricepulse.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def update_all_prices():
    app = create_app()
    scraper = PriceComparisonScraper()

    with app.app_context():
        products = Product.query.all()
        print(f"Found {len(products)} products to update")
        updated = 0
        skipped = 0
        failed = 0

        for p in products:
            try:
                # Use scraper to get latest prices for the product URLs
                amazon_url = getattr(p, 'amazon_url', None)
                flipkart_url = getattr(p, 'flipkart_url', None)

                result = scraper.get_price_comparison(amazon_url, flipkart_url)
                new_am = result.get('amazon_price')
                new_fk = result.get('flipkart_price')

                am_changed = (new_am is not None) and (new_am != p.amazon_price)
                fk_changed = (new_fk is not None) and (new_fk != p.flipkart_price)

                if am_changed or fk_changed:
                    # create PriceHistory row
                    ph = PriceHistory(product_id=p.id,
                                      amazon_price=new_am if new_am is not None else p.amazon_price,
                                      flipkart_price=new_fk if new_fk is not None else p.flipkart_price,
                                      source='scraper')
                    p.amazon_price = new_am if new_am is not None else p.amazon_price
                    p.flipkart_price = new_fk if new_fk is not None else p.flipkart_price
                    db.session.add(ph)
                    db.session.add(p)
                    db.session.commit()
                    updated += 1
                    print(f"Updated product {p.id} - {p.product_name}: amazon={p.amazon_price}, flipkart={p.flipkart_price}")
                else:
                    skipped += 1

                # be polite between requests
                time.sleep(1)

            except Exception as e:
                failed += 1
                print(f"Failed updating product {p.id} - {p.product_name}: {e}")

        print(f"Done. updated={updated}, skipped={skipped}, failed={failed}")


if __name__ == '__main__':
    update_all_prices()
