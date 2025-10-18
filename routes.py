from flask import Blueprint, request, jsonify
from models import Product, PriceHistory, db

def register_routes(app):
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    @api_bp.route('/products', methods=['GET'])
    def get_products():
        try:
            category = request.args.get('category')
            search = request.args.get('search', '').strip()
            sort_by = request.args.get('sort', 'name')
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            brands = request.args.getlist('brands')
            
            query = Product.query
            
            if category and category != 'All':
                query = query.filter(Product.category == category)
            
            if search:
                query = query.filter(Product.product_name.ilike(f'%{search}%'))
            
            if brands:
                query = query.filter(Product.brand.in_(brands))
            
            if min_price is not None:
                query = query.filter(
                    db.or_(Product.amazon_price >= min_price, Product.flipkart_price >= min_price)
                )
            
            if max_price is not None:
                query = query.filter(
                    db.or_(Product.amazon_price <= max_price, Product.flipkart_price <= max_price)
                )
            
            if sort_by == 'name':
                query = query.order_by(Product.product_name)
            elif sort_by == 'brand':
                query = query.order_by(Product.brand, Product.product_name)
            elif sort_by == 'amazon-low':
                query = query.order_by(Product.amazon_price)
            elif sort_by == 'amazon-high':
                query = query.order_by(Product.amazon_price.desc())
            elif sort_by == 'flipkart-low':
                query = query.order_by(Product.flipkart_price)
            elif sort_by == 'flipkart-high':
                query = query.order_by(Product.flipkart_price.desc())
            elif sort_by == 'price-diff':
                query = query.order_by((Product.amazon_price - Product.flipkart_price).desc())
            
            products = query.all()
            return jsonify([product.to_dict() for product in products])
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        try:
            product = Product.query.get_or_404(product_id)
            return jsonify(product.to_dict())
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/brands', methods=['GET'])
    def get_brands():
        try:
            category = request.args.get('category')
            query = db.session.query(Product.brand).distinct()
            
            if category and category != 'All':
                query = query.filter(Product.category == category)
            
            brands = [row[0] for row in query.all() if row[0]]
            return jsonify(sorted(brands))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/categories', methods=['GET'])
    def get_categories():
        try:
            categories = db.session.query(Product.category).distinct().all()
            return jsonify([cat[0] for cat in categories])
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/compare', methods=['POST'])
    def compare_products():
        try:
            data = request.get_json()
            product_ids = data.get('productIds', [])
            
            if len(product_ids) < 2 or len(product_ids) > 4:
                return jsonify({'error': 'Please select 2-4 products to compare'}), 400
            
            products = Product.query.filter(Product.id.in_(product_ids)).all()
            
            if len(products) != len(product_ids):
                return jsonify({'error': 'Some products not found'}), 404
            
            comparison_data = []
            for product in products:
                comparison_data.append({
                    'id': product.id,
                    'category': product.category,
                    'productName': product.product_name,
                    'brand': product.brand,
                    'amazonPrice': product.amazon_price,
                    'amazonUrl': product.amazon_url,
                    'amazonCoupon': product.amazon_coupon,
                    'flipkartPrice': product.flipkart_price,
                    'flipkartUrl': product.flipkart_url,
                    'flipkartCoupon': product.flipkart_coupon,
                    'priceDifference': abs(product.amazon_price - product.flipkart_price),
                    'bestPrice': min(product.amazon_price, product.flipkart_price),
                    'bestPlatform': 'Amazon' if product.amazon_price < product.flipkart_price else 'Flipkart'
                })
            
            return jsonify(comparison_data)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/search', methods=['GET'])
    def search_products():
        try:
            search_term = request.args.get('q', '').strip()
            
            if not search_term:
                return jsonify([])
            
            products = Product.query.filter(
                db.or_(
                    Product.product_name.ilike(f'%{search_term}%'),
                    Product.brand.ilike(f'%{search_term}%')
                )
            ).limit(20).all()
            
            results = []
            for product in products:
                results.append({
                    'id': product.id,
                    'productName': product.product_name,
                    'brand': product.brand,
                    'category': product.category,
                    'bestPrice': min(product.amazon_price, product.flipkart_price)
                })
            
            return jsonify(results)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    app.register_blueprint(api_bp)
