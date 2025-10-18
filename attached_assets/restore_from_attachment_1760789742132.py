import sys
import os
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


def find_product(session, amazon_url, flipkart_url, product_name):
    # 1) exact match by amazon_url
    if amazon_url:
        p = session.query(Product).filter(Product.amazon_url == amazon_url).first()
        if p:
            return p

    # 2) exact match by flipkart_url
    if flipkart_url:
        p = session.query(Product).filter(Product.flipkart_url == flipkart_url).first()
        if p:
            return p

    # 3) case-insensitive exact product name
    if product_name:
        p = session.query(Product).filter(Product.product_name.ilike(product_name)).first()
        if p:
            return p

    # 4) case-insensitive contains
    if product_name:
        p = session.query(Product).filter(Product.product_name.ilike(f"%{product_name}%")).first()
        if p:
            return p

    # not found
    return None


def restore_from_file(db_path, file_path, commit=False):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    total = 0
    updated = 0
    created = 0
    skipped = 0
    details = []
    matched_product_ids = set()

    with app.app_context():
        with open(file_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            for row in rows:
                total += 1
                category = row.get('Category') or row.get('category')
                product_name = (row.get('Product_Name') or row.get('Product_Name'.lower()) or row.get('Product Name') or row.get('product_name') or '').strip()
                amazon_price = parse_price(row.get('Amazon_Price') or row.get('amazon_price'))
                amazon_url = (row.get('Amazon_URL') or row.get('Amazon_URL'.lower()) or row.get('amazon_url') or '').strip()
                flipkart_price = parse_price(row.get('Flipkart_Price') or row.get('flipkart_price'))
                flipkart_url = (row.get('Flipkart_URL') or row.get('flipkart_url') or '').strip()
                brand = (row.get('Brand') or row.get('brand') or '').strip()

                product = find_product(db.session, amazon_url, flipkart_url, product_name)
                if not product:
                    # mark as skipped for now; creation handled in sync mode later
                    skipped += 1
                    details.append((product_name, 'NO_MATCH'))
                    continue

                matched_product_ids.add(product.id)

                # record pre-update snapshot
                ph = PriceHistory(product_id=product.id,
                                  amazon_price=product.amazon_price,
                                  flipkart_price=product.flipkart_price,
                                  recorded_at=datetime.utcnow(),
                                  source='pre_restore_attachment')
                db.session.add(ph)

                # update fields from CSV if present
                changed = False
                # ensure numeric fallback
                if amazon_price is None:
                    amazon_price = product.amazon_price
                if flipkart_price is None:
                    flipkart_price = product.flipkart_price

                if product.amazon_price != amazon_price:
                    product.amazon_price = amazon_price
                    changed = True
                if product.flipkart_price != flipkart_price:
                    product.flipkart_price = flipkart_price
                    changed = True
                if amazon_url and product.amazon_url != amazon_url:
                    product.amazon_url = amazon_url
                    changed = True
                if flipkart_url and product.flipkart_url != flipkart_url:
                    product.flipkart_url = flipkart_url
                    changed = True
                if brand and product.brand != brand:
                    product.brand = brand
                    changed = True

                if changed:
                    updated += 1
                    details.append((product_name, f'UPDATED pid={product.id}'))
                else:
                    details.append((product_name, f'NOCHANGE pid={product.id}'))

        # commit pre-update snapshots and updates if commit
        if commit:
            db.session.commit()

    # return matched ids and rows for possible sync operations
    return {
        'total_rows': total,
        'updated': updated,
        'created': created,
        'skipped': skipped,
        'details_sample': details[:20],
        'matched_product_ids': matched_product_ids,
        'rows': rows
    }

    # Summary
    return {
        'total_rows': total,
        'updated': updated,
        'skipped': skipped,
        'details_sample': details[:20]
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Restore/update existing products from CSV attachment (no new products will be created).')
    parser.add_argument('--file', '-f', required=True, help='Path to CSV file')
    parser.add_argument('--db', default='pricepulse.db', help='Path to sqlite DB file (relative)')
    parser.add_argument('--yes', action='store_true', help='Apply changes (without --yes the script runs a dry-run)')
    parser.add_argument('--sync', action='store_true', help='Synchronize DB to match the CSV: create missing, update existing, delete extras')

    args = parser.parse_args()

    file_path = args.file
    db_path = args.db

    if not os.path.exists(file_path):
        print('ERROR: file not found:', file_path)
        sys.exit(2)

    print('DRY-RUN' if not args.yes else 'APPLYING CHANGES')
    print('Reading file:', file_path)
    res = restore_from_file(db_path, file_path, commit=args.yes)

    # If sync requested, compute create/delete candidates
    create_candidates = []
    delete_candidates = []
    if args.sync:
        # Build a map of keys from CSV for quick lookup
        csv_keys = set()
        for r in res['rows']:
            key = ( (r.get('Amazon_URL') or '').strip(), (r.get('Flipkart_URL') or '').strip(), (r.get('Product_Name') or '').strip().lower() )
            csv_keys.add(key)

        # find existing products not matched
        import sqlite3
        # load product list via SQLAlchemy
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        with app.app_context():
            all_products = db.session.query(Product).all()
            for p in all_products:
                key = ( (p.amazon_url or '').strip(), (p.flipkart_url or '').strip(), (p.product_name or '').strip().lower() )
                if p.id in res['matched_product_ids']:
                    continue
                # If product key not in CSV, mark for deletion in sync
                if key not in csv_keys:
                    delete_candidates.append((p.id, p.product_name))

        # creation candidates are CSV rows that had NO_MATCH earlier
        for r, d in zip(res['rows'], res['details_sample'] + [None]*len(res['rows'])):
            # this loop won't be used to deduce creates accurately here; recompute
            if (r.get('Amazon_URL') or '').strip() == '' and (r.get('Flipkart_URL') or '').strip() == '':
                continue
        # Simpler: creation count = number of rows in CSV that did not match any existing product
        create_count = sum(1 for r in res['rows'] if (find_product.__code__ and False))
        # We will not attempt to estimate creates here; we'll detect and create during commit phase below.

    print('Done. Summary:')
    print(' Total rows in file:', res['total_rows'])
    print(' Updated rows (matched and changed):', res['updated'])
    print(' Rows with no existing match (would be created in sync):', res['skipped'])
    if args.sync:
        print(' Products that would be deleted (not present in CSV):', len(delete_candidates))
        if len(delete_candidates) > 0:
            print('  Sample deletions:', delete_candidates[:10])
    for d in res['details_sample']:
        print('  ', d[0], '->', d[1])

    # If sync + yes, perform create/delete operations now
    if args.sync and args.yes:
        print('\nApplying sync changes...')
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        with app.app_context():
            # reload rows and create/update
            with open(file_path, newline='', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    product_name = (row.get('Product_Name') or row.get('product_name') or '').strip()
                    amazon_price = parse_price(row.get('Amazon_Price') or row.get('amazon_price')) or 0.0
                    amazon_url = (row.get('Amazon_URL') or row.get('amazon_url') or '').strip()
                    flipkart_price = parse_price(row.get('Flipkart_Price') or row.get('flipkart_price')) or 0.0
                    flipkart_url = (row.get('Flipkart_URL') or row.get('flipkart_url') or '').strip()
                    category = row.get('Category') or row.get('category') or 'Uncategorized'
                    brand = (row.get('Brand') or row.get('brand') or '').strip()

                    product = find_product(db.session, amazon_url, flipkart_url, product_name)
                    if product:
                        # already handled pre-update snapshots
                        # update fields
                        product.amazon_price = amazon_price
                        product.flipkart_price = flipkart_price
                        product.amazon_url = amazon_url or product.amazon_url
                        product.flipkart_url = flipkart_url or product.flipkart_url
                        product.brand = brand or product.brand
                    else:
                        # create new product
                        newp = Product(category=category, product_name=product_name, brand=brand,
                                       amazon_price=amazon_price, amazon_url=amazon_url or '',
                                       flipkart_price=flipkart_price, flipkart_url=flipkart_url or '')
                        db.session.add(newp)

            # delete extras
            for pid, name in delete_candidates:
                p = db.session.query(Product).get(pid)
                if p:
                    ph = PriceHistory(product_id=p.id, amazon_price=p.amazon_price, flipkart_price=p.flipkart_price, recorded_at=datetime.utcnow(), source='pre_delete_sync')
                    db.session.add(ph)
                    db.session.delete(p)

            db.session.commit()
        print('Sync applied.')
