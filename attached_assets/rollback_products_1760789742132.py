#!/usr/bin/env python3
"""Rollback product prices to previous PriceHistory snapshots.

Usage examples:
  # Dry-run: show what would be changed for all products, stepping back 1 snapshot
  python scripts/rollback_products.py --all --steps 1 --dry-run

  # Rollback two steps for product ids 1 and 2, commit changes
  python scripts/rollback_products.py --product-ids 1 2 --steps 2

Options:
  --steps N        Number of history steps to roll back (default 1)
  --product-ids    One or more product IDs to target
  --all            Rollback all products
  --dry-run        Do not commit changes; only print the planned operations
  --yes            Skip confirmation prompt when committing
"""
import argparse
import sys
import os
from typing import List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask
from models import db, Product, PriceHistory


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'rollback'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricepulse.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def parse_args():
    p = argparse.ArgumentParser(description='Rollback product prices to previous PriceHistory snapshots')
    p.add_argument('--steps', type=int, default=1, help='Number of history steps to roll back (default 1)')
    p.add_argument('--product-ids', nargs='*', type=int, help='Product IDs to rollback')
    p.add_argument('--all', action='store_true', help='Rollback all products')
    p.add_argument('--dry-run', action='store_true', help='Show planned changes but do not commit')
    p.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    return p.parse_args()


def gather_targets(args) -> List[Product]:
    if args.all:
        return Product.query.all()
    if args.product_ids:
        return Product.query.filter(Product.id.in_(args.product_ids)).all()
    raise SystemExit('No targets specified. Use --all or --product-ids')


def rollback_product(p: Product, steps: int):
    # Retrieve history ordered newest first
    history = PriceHistory.query.filter_by(product_id=p.id).order_by(PriceHistory.recorded_at.desc()).all()
    if len(history) <= steps:
        return None  # not enough history to rollback

    # Target snapshot is the entry at index `steps` (0 = latest, 1 = previous)
    target = history[steps]
    old_am = p.amazon_price
    old_fk = p.flipkart_price
    new_am = target.amazon_price
    new_fk = target.flipkart_price

    changed = (new_am is not None and new_am != old_am) or (new_fk is not None and new_fk != old_fk)

    return {
        'product_id': p.id,
        'product_name': p.product_name,
        'old_amazon_price': old_am,
        'old_flipkart_price': old_fk,
        'new_amazon_price': new_am,
        'new_flipkart_price': new_fk,
        'changed': changed,
        'target_recorded_at': target.recorded_at,
        'target_source': target.source
    }


def apply_rollback(p: Product, snapshot: dict):
    # apply values and create a PriceHistory row recording the rollback
    p.amazon_price = snapshot['new_amazon_price'] if snapshot['new_amazon_price'] is not None else p.amazon_price
    p.flipkart_price = snapshot['new_flipkart_price'] if snapshot['new_flipkart_price'] is not None else p.flipkart_price
    ph = PriceHistory(product_id=p.id, amazon_price=p.amazon_price, flipkart_price=p.flipkart_price, source=f"rollback:steps")
    db.session.add(ph)
    db.session.add(p)


def main():
    args = parse_args()

    app = create_app()
    with app.app_context():
        targets = gather_targets(args)
        planned = []

        for p in targets:
            snap = rollback_product(p, args.steps)
            if snap is None:
                planned.append({'product_id': p.id, 'product_name': p.product_name, 'skipped': True, 'reason': 'not enough history'})
            else:
                planned.append(snap)

        # Print summary
        print('Rollback plan:')
        for item in planned:
            if item.get('skipped'):
                print(f"- SKIP {item['product_id']} {item['product_name']}: {item['reason']}")
            else:
                ch = 'WILL CHANGE' if item['changed'] else 'NO CHANGE'
                print(f"- {item['product_id']} {item['product_name']}: {ch} => amazon {item['old_amazon_price']} -> {item['new_amazon_price']}, flipkart {item['old_flipkart_price']} -> {item['new_flipkart_price']} (source {item['target_source']} at {item['target_recorded_at']})")

        if args.dry_run:
            print('\nDry-run mode: no changes committed')
            return

        to_apply = [item for item in planned if not item.get('skipped') and item.get('changed')]
        if not to_apply:
            print('Nothing to apply.')
            return

        if not args.yes:
            ans = input(f"Apply rollback to {len(to_apply)} products? Type YES to proceed: ")
            if ans.strip() != 'YES':
                print('Aborted by user')
                return

        # Apply changes
        applied = 0
        for item in to_apply:
            p = Product.query.get(item['product_id'])
            apply_rollback(p, item)
            applied += 1

        db.session.commit()
        print(f'Applied rollback to {applied} products')


if __name__ == '__main__':
    main()
