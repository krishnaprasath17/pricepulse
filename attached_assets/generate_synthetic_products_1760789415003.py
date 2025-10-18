#!/usr/bin/env python3
"""
Generate synthetic realistic-looking products (Phones, Laptops, Headphones)
and insert them into the local SQLite DB to provide a richer catalog for UI
development and demos.

Run:
  D:/PricePulse/PricePulse/.venv/Scripts/python.exe generate_synthetic_products.py
"""

import random
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Product
from flask import Flask


def create_app_for_db():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'synthetic-seed-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricepulse.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


PHONE_MODELS = [
    'Galaxy S', 'Galaxy A', 'Galaxy M', 'iPhone', 'Pixel', 'OnePlus', 'Redmi Note', 'POCO X', 'realme', 'Vivo Y'
]

LAPTOP_MODELS = [
    'Inspiron', 'ThinkBook', 'MacBook Air', 'MacBook Pro', 'VivoBook', 'Aspire', 'Nitro', 'Legion', 'ROG', 'Pavilion'
]

HEADPHONE_MODELS = [
    'Airdopes', 'AirPods', 'WH-1000XM', 'JBL Tune', 'Soundcore', 'Rockerz', 'Buds', 'QuietComfort', 'Momentum'
]

BRANDS = ['Samsung', 'Apple', 'OnePlus', 'Xiaomi', 'POCO', 'realme', 'vivo', 'Google', 'HP', 'Dell', 'Lenovo', 'ASUS', 'Acer', 'Sony', 'JBL', 'boAt', 'Anker', 'Noise']


def make_phone(i: int):
    brand = random.choice(BRANDS[:8])
    model = random.choice(PHONE_MODELS)
    name = f"{brand} {model} {random.randint(1, 999)}"
    price = random.randint(7000, 80000)
    return {
        'category': 'Phones',
        'product_name': name,
        'brand': brand,
        'amazon_price': price,
        'amazon_url': f'https://www.amazon.in/dp/PHONE{i}',
        'flipkart_price': int(price * random.uniform(0.95, 1.05)),
        'flipkart_url': f'https://www.flipkart.com/item/PHONE{i}'
    }


def make_laptop(i: int):
    brand = random.choice(BRANDS[8:14])
    model = random.choice(LAPTOP_MODELS)
    name = f"{brand} {model} {random.choice(['14','15','16','X'])} {random.choice(['Pro','Plus','G','Air','Neo'])}"
    price = random.randint(30000, 250000)
    return {
        'category': 'Laptops',
        'product_name': name,
        'brand': brand,
        'amazon_price': price,
        'amazon_url': f'https://www.amazon.in/dp/LAP{i}',
        'flipkart_price': int(price * random.uniform(0.95, 1.05)),
        'flipkart_url': f'https://www.flipkart.com/item/LAP{i}'
    }


def make_headphone(i: int):
    brand = random.choice(BRANDS[14:])
    model = random.choice(HEADPHONE_MODELS)
    name = f"{brand} {model} {random.randint(100,999)}"
    price = random.randint(500, 30000)
    return {
        'category': 'Headphones',
        'product_name': name,
        'brand': brand,
        'amazon_price': price,
        'amazon_url': f'https://www.amazon.in/dp/HPH{i}',
        'flipkart_price': int(price * random.uniform(0.9, 1.1)),
        'flipkart_url': f'https://www.flipkart.com/item/HPH{i}'
    }


def main():
    app = create_app_for_db()
    total_to_create = 150
    phones = int(total_to_create * 0.4)
    laptops = int(total_to_create * 0.35)
    headphones = total_to_create - phones - laptops

    created = 0

    with app.app_context():
        db.create_all()
        # simple dedupe by product_name
        existing_names = {p.product_name for p in db.session.query(Product.product_name).all()}

        idx = 0
        for i in range(phones):
            idx += 1
            data = make_phone(idx)
            if data['product_name'] in existing_names:
                continue
            product = Product(**data)
            db.session.add(product)
            created += 1

        for i in range(laptops):
            idx += 1
            data = make_laptop(idx)
            if data['product_name'] in existing_names:
                continue
            product = Product(**data)
            db.session.add(product)
            created += 1

        for i in range(headphones):
            idx += 1
            data = make_headphone(idx)
            if data['product_name'] in existing_names:
                continue
            product = Product(**data)
            db.session.add(product)
            created += 1

        db.session.commit()

    print(f"✅ Created {created} synthetic products and committed to pricepulse.db")


if __name__ == '__main__':
    main()
