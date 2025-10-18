from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# This will be initialized by the app
db = SQLAlchemy()

class Product(db.Model):
    """Product model for storing price comparison data"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    product_name = db.Column(db.String(255), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=True, index=True)
    asin = db.Column(db.String(64), nullable=True, index=True)
    source = db.Column(db.String(32), nullable=True, index=True)
    amazon_price = db.Column(db.Float, nullable=False)
    amazon_url = db.Column(db.Text, nullable=False)
    flipkart_price = db.Column(db.Float, nullable=False)
    flipkart_url = db.Column(db.Text, nullable=False)
    # Coupon fields (nullable) - support simple coupons per product
    coupon_code = db.Column(db.String(100), nullable=True, index=True)
    coupon_type = db.Column(db.String(20), nullable=True)  # 'percent' or 'fixed'
    coupon_amount = db.Column(db.Float, nullable=True)
    coupon_platform = db.Column(db.String(32), nullable=True)  # 'Amazon', 'Flipkart', 'Both'
    coupon_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.product_name}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'category': self.category,
            'productName': self.product_name,
            'brand': self.brand,
            'asin': self.asin,
            'amazonPrice': self.amazon_price,
            'amazonUrl': self.amazon_url,
            'flipkartPrice': self.flipkart_price,
            'flipkartUrl': self.flipkart_url,
            'couponCode': self.coupon_code,
            'couponType': self.coupon_type,
            'couponAmount': self.coupon_amount,
            'couponPlatform': self.coupon_platform,
            'couponExpires': self.coupon_expires.isoformat() if self.coupon_expires else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class PriceHistory(db.Model):
    """Price history model for tracking price changes over time"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    amazon_price = db.Column(db.Float, nullable=False)
    flipkart_price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(32), nullable=True)
    
    # Relationship
    product = db.relationship('Product', backref=db.backref('price_history', lazy=True))
    
    def __repr__(self):
        return f'<PriceHistory {self.product_id} - {self.recorded_at}>'
