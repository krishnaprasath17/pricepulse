from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    product_name = db.Column(db.String(255), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=True, index=True)
    
    amazon_price = db.Column(db.Float, nullable=False)
    amazon_url = db.Column(db.Text, nullable=False)
    amazon_coupon = db.Column(db.String(255), nullable=True)
    
    flipkart_price = db.Column(db.Float, nullable=False)
    flipkart_url = db.Column(db.Text, nullable=False)
    flipkart_coupon = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    price_history = db.relationship('PriceHistory', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.product_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'productName': self.product_name,
            'brand': self.brand,
            'amazonPrice': self.amazon_price,
            'amazonUrl': self.amazon_url,
            'amazonCoupon': self.amazon_coupon,
            'flipkartPrice': self.flipkart_price,
            'flipkartUrl': self.flipkart_url,
            'flipkartCoupon': self.flipkart_coupon,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    amazon_price = db.Column(db.Float, nullable=False)
    flipkart_price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), default='manual')
    
    def __repr__(self):
        return f'<PriceHistory {self.product_id} - {self.recorded_at}>'
