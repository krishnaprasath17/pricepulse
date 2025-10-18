from flask import Flask, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import db, Product


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@localhost/pricepulse')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db and extensions
    db.init_app(app)
    CORS(app)

    # Register routes from routes.py
    from routes import register_routes
    register_routes(app)

    return app


app = create_app()

@app.route('/')
def home():
    """Main page route"""
    return render_template('index.html')
