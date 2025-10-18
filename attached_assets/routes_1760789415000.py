from flask import Blueprint, request, jsonify, session
from models import Product, PriceHistory, db
from datetime import datetime
import json

def register_routes(app):
    """Register all application routes"""
    
    # API Blueprint
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    @api_bp.route('/products', methods=['GET'])
    def get_products():
        """Get products with filtering and sorting"""
        try:
            # Get query parameters
            category = request.args.get('category')
            search = request.args.get('search', '').strip()
            sort_by = request.args.get('sort', 'name')
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            brands = request.args.getlist('brands')
            
            # Build query
            query = Product.query
            
            # Apply filters
            if category and category != 'All':
                query = query.filter(Product.category == category)
            
            if search:
                query = query.filter(Product.product_name.ilike(f'%{search}%'))
            
            if brands:
                query = query.filter(Product.brand.in_(brands))
            
            if min_price is not None:
                query = query.filter(Product.amazon_price >= min_price)
            
            if max_price is not None:
                query = query.filter(Product.amazon_price <= max_price)
            
            # Apply sorting
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
                # Sort by price difference (largest difference first)
                query = query.order_by((Product.amazon_price - Product.flipkart_price).desc())
            
            products = query.all()
            
            # Convert to dict format
            products_data = []
            for product in products:
                # compute discounted price helper
                def apply_coupon(price, coupon_type, coupon_amount):
                    try:
                        if coupon_type is None or coupon_amount is None:
                            return None
                        if coupon_type == 'percent':
                            return round(price * (1.0 - float(coupon_amount) / 100.0), 2)
                        else:
                            return round(max(0.0, price - float(coupon_amount)), 2)
                    except Exception:
                        return None

                amazon_discounted = None
                flipkart_discounted = None
                if product.coupon_code:
                    # apply to both or specific platform
                    if product.coupon_platform in (None, 'Both', 'Amazon'):
                        amazon_discounted = apply_coupon(product.amazon_price, product.coupon_type, product.coupon_amount)
                    if product.coupon_platform in (None, 'Both', 'Flipkart'):
                        flipkart_discounted = apply_coupon(product.flipkart_price, product.coupon_type, product.coupon_amount)

                products_data.append({
                    'id': product.id,
                    'category': product.category,
                    'productName': product.product_name,
                    'brand': product.brand,
                    'amazonPrice': product.amazon_price,
                    'amazonUrl': product.amazon_url,
                    'flipkartPrice': product.flipkart_price,
                    'flipkartUrl': product.flipkart_url,
                    'couponCode': product.coupon_code,
                    'couponType': product.coupon_type,
                    'couponAmount': product.coupon_amount,
                    'couponPlatform': product.coupon_platform,
                    'couponExpires': product.coupon_expires.isoformat() if product.coupon_expires else None,
                    'amazonDiscountedPrice': amazon_discounted,
                    'flipkartDiscountedPrice': flipkart_discounted,
                    'bestPriceWithCoupon': min([p for p in [amazon_discounted or product.amazon_price, flipkart_discounted or product.flipkart_price] if p is not None])
                })
            
            return jsonify(products_data)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        """Get a specific product by ID"""
        try:
            product = Product.query.get_or_404(product_id)
            return jsonify(product.to_dict())
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/brands', methods=['GET'])
    def get_brands():
        """Get available brands by category"""
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
        """Get available categories"""
        try:
            categories = db.session.query(Product.category).distinct().all()
            return jsonify([cat[0] for cat in categories])
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/compare', methods=['POST'])
    def compare_products():
        """Compare multiple products"""
        try:
            data = request.get_json()
            product_ids = data.get('productIds', [])
            
            if len(product_ids) < 2 or len(product_ids) > 4:
                return jsonify({'error': 'Please select 2-4 products to compare'}), 400
            
            products = Product.query.filter(Product.id.in_(product_ids)).all()
            
            if len(products) != len(product_ids):
                return jsonify({'error': 'Some products not found'}), 404
            
            # Helper to compute discounted price (returns None if no coupon or not applicable)
            def apply_coupon(price, coupon_type, coupon_amount):
                try:
                    if coupon_type is None or coupon_amount is None:
                        return None
                    if coupon_type == 'percent':
                        return round(price * (1.0 - float(coupon_amount) / 100.0), 2)
                    else:
                        # fixed amount off
                        return round(max(0.0, price - float(coupon_amount)), 2)
                except Exception:
                    return None

            comparison_data = []
            for product in products:
                # Compute discounted prices if coupon applies to the platform
                coupon_code = product.coupon_code
                coupon_type = product.coupon_type
                coupon_amount = product.coupon_amount
                coupon_platform = product.coupon_platform

                amazon_discounted = None
                flipkart_discounted = None
                if coupon_code:
                    if coupon_platform in (None, 'Both', 'Amazon'):
                        amazon_discounted = apply_coupon(product.amazon_price, coupon_type, coupon_amount)
                    if coupon_platform in (None, 'Both', 'Flipkart'):
                        flipkart_discounted = apply_coupon(product.flipkart_price, coupon_type, coupon_amount)

                # Determine best prices (original and with coupon)
                orig_best = min(product.amazon_price, product.flipkart_price)
                # best considering coupons where available
                candidate_amazon = amazon_discounted if amazon_discounted is not None else product.amazon_price
                candidate_flipkart = flipkart_discounted if flipkart_discounted is not None else product.flipkart_price
                best_with_coupon = min(candidate_amazon, candidate_flipkart)
                best_platform_with_coupon = 'Amazon' if candidate_amazon < candidate_flipkart else 'Flipkart'

                comparison_data.append({
                    'id': product.id,
                    'category': product.category,
                    'productName': product.product_name,
                    'brand': product.brand,
                    'amazonPrice': product.amazon_price,
                    'amazonUrl': product.amazon_url,
                    'flipkartPrice': product.flipkart_price,
                    'flipkartUrl': product.flipkart_url,
                    'priceDifference': abs(product.amazon_price - product.flipkart_price),
                    'bestPrice': orig_best,
                    'bestPlatform': 'Amazon' if product.amazon_price < product.flipkart_price else 'Flipkart',
                    # coupon fields
                    'couponCode': coupon_code,
                    'couponType': coupon_type,
                    'couponAmount': coupon_amount,
                    'couponPlatform': coupon_platform,
                    'couponExpires': product.coupon_expires.isoformat() if product.coupon_expires else None,
                    # discounted prices
                    'amazonDiscountedPrice': amazon_discounted,
                    'flipkartDiscountedPrice': flipkart_discounted,
                    # best with coupon
                    'bestPriceWithCoupon': best_with_coupon,
                    'bestPlatformWithCoupon': best_platform_with_coupon
                })
            
            return jsonify(comparison_data)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/search', methods=['GET'])
    def search_products():
        """Advanced search endpoint"""
        try:
            query_params = request.args
            search_term = query_params.get('q', '').strip()
            
            if not search_term:
                return jsonify([])
            
            # Search in product name and brand
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
    
    # Register the blueprint
    app.register_blueprint(api_bp)
