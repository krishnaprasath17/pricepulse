#!/usr/bin/env python3
"""Update product URLs and prices using adapters and scraper fallback.

This script will:
 - Load all products from the DB
 - For each product, search Amazon and Flipkart by product name (adapter first)
 - Update the product record fields (url, price, asin, brand, image) when the best match is found
 - Create a PriceHistory row if the price changes

Note: using official APIs (ENV keys) is preferred. If keys are absent, scraper fallback will be used
which may be rate-limited or blocked.
"""
import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, Product, PriceHistory
from services.api_integrations import search_amazon, search_flipkart


def create_app():
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'update-urls'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricepulse.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def choose_best_hit(hits, product_name):
    # naive best-hit: prefer exact title match, then first hit
    if not hits:
        return None
    for h in hits:
        title = h.get('title') or h.get('product_name') or ''
        if title and title.lower() == product_name.lower():
            return h
    return hits[0]


def update_products():
    app = create_app()
    with app.app_context():
        products = Product.query.all()
        total = len(products)
        updated = 0
        skipped = 0
        failed = 0

        for p in products:
            try:
                name = p.product_name
                # search Amazon
                am_hits = []
                try:
                    am_hits = search_amazon(name, max_results=3)
                except Exception as e:
                    print(f"Amazon search failed for '{name}': {e}")

                fk_hits = []
                try:
                    fk_hits = search_flipkart(name, max_results=3)
                except Exception as e:
                    print(f"Flipkart search failed for '{name}': {e}")

                am_best = choose_best_hit(am_hits, name)
                fk_best = choose_best_hit(fk_hits, name)

                changed = False

                if am_best:
                    new_price = am_best.get('price')
                    new_url = am_best.get('url')
                    new_asin = am_best.get('asin') or getattr(p, 'asin', None)
                    new_brand = am_best.get('brand') or getattr(p, 'brand', None)
                    new_image = am_best.get('image') or None

                    if new_price is not None and new_price != p.amazon_price:
                        changed = True
                    if new_url and new_url != p.amazon_url:
                        changed = True

                    p.amazon_price = new_price or p.amazon_price
                    p.amazon_url = new_url or p.amazon_url
                    try:
                        setattr(p, 'asin', new_asin)
                    except Exception:
                        pass
                    p.brand = new_brand or p.brand
                    # image may be stored elsewhere on product table in future

                if fk_best:
                    new_price = fk_best.get('price')
                    new_url = fk_best.get('url')
                    new_brand = fk_best.get('brand') or p.brand
                    new_image = fk_best.get('image') or None

                    if new_price is not None and new_price != p.flipkart_price:
                        changed = True
                    if new_url and new_url != p.flipkart_url:
                        changed = True

                    p.flipkart_price = new_price or p.flipkart_price
                    p.flipkart_url = new_url or p.flipkart_url
                    p.brand = new_brand or p.brand

                if changed:
                    # create PriceHistory with new snapshot
                    ph = PriceHistory(product_id=p.id, amazon_price=p.amazon_price, flipkart_price=p.flipkart_price, source='update-script')
                    db.session.add(ph)
                    db.session.add(p)
                    db.session.commit()
                    updated += 1
                    print(f"Updated product {p.id}: {p.product_name}")
                else:
                    skipped += 1

                # be polite
                time.sleep(0.5)

            except Exception as e:
                failed += 1
                print(f"Failed processing product {p.id} - {p.product_name}: {e}")

        print(f"Finished. total={total}, updated={updated}, skipped={skipped}, failed={failed}")


if __name__ == '__main__':
    update_products()
