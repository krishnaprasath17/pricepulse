# PricePulse - E-commerce Price Comparison Platform

## Overview

PricePulse is a Flask-based web application that helps users find the best deals on electronics by comparing prices between Amazon and Flipkart. The platform allows users to search, filter, and compare products across multiple categories (Phones, Laptops, Headphones) to identify the best purchasing options and maximize savings.

The application features a responsive web interface with advanced filtering capabilities, product comparison tools, and price history tracking. It combines web scraping capabilities with a clean, user-friendly interface to provide real-time price comparisons.

## Recent Changes

**October 18, 2025:**
- ✅ Complete Flask application implemented with all core features
- ✅ Database models created with coupon support (amazon_coupon, flipkart_coupon fields)
- ✅ All API endpoints implemented and tested (/api/products, /api/brands, /api/categories, /api/compare)
- ✅ Bootstrap 5 frontend with responsive design and coupon display badges
- ✅ Imported 147 products across 3 categories (Phones: 50, Laptops: 50, Headphones: 47)
- ✅ Selenium-based web scraper for Amazon and Flipkart price updates
- ✅ Application running successfully on port 5000
- ✅ All code reviewed and approved by architect

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- HTML5 with Jinja2 templating
- Bootstrap 5 for responsive UI components
- Vanilla JavaScript for client-side functionality
- Font Awesome for icons
- Custom CSS with CSS variables for theming

**Key Components:**
- Category-based navigation and filtering
- Product search with debounced input
- Multi-sort options (by name, brand, price, platform)
- Dynamic brand filtering
- Price range slider filtering
- Side-by-side product comparison modal (up to 4 products)
- Responsive card-based product grid layout

**Design Decisions:**
- **Bootstrap 5 Framework**: Chosen for rapid development with consistent, mobile-first responsive design. Provides ready-made components and grid system without heavy JavaScript framework overhead.
- **Vanilla JavaScript Class Pattern**: Used `PricePulseApp` class to organize client-side logic without framework dependencies. Enables straightforward API integration and DOM manipulation with minimal bundle size.
- **Server-Side Rendering**: Jinja2 templates render initial HTML on server, improving first-load performance and SEO while maintaining simplicity.

### Backend Architecture

**Technology Stack:**
- Python 3.8+ with Flask web framework
- Flask-SQLAlchemy for ORM
- Flask-CORS for cross-origin support
- SQLite database (development) with easy migration path to MySQL (production)

**Database Schema:**
- **Product Model**: Stores product information with Amazon and Flipkart pricing data, URLs, coupons, brand extraction, and timestamps
- **PriceHistory Model**: Tracks price changes over time for trend analysis (referenced but not fully shown in codebase)
- Indexed fields: category, product_name, brand for optimized queries

**API Design:**
- RESTful API with `/api` prefix Blueprint pattern
- `GET /api/products` - Query products with filtering, sorting, pagination
- `GET /api/brands` - Retrieve available brands (implied from routes)
- `POST /api/compare` - Compare multiple products by IDs
- Query parameter filtering: category, search, sort, brands[], min_price, max_price

**Key Design Decisions:**
- **SQLite for Development**: Enables zero-configuration local development with easy file-based database. Production can switch to MySQL via environment variable configuration.
- **Application Factory Pattern**: `create_app()` function allows multiple app instances for testing and provides clean separation of configuration concerns.
- **Blueprint Organization**: API routes registered via Blueprint pattern (`register_routes(app)`) enables modular route organization and easier testing.
- **ORM with SQLAlchemy**: Provides database abstraction, migration support, and prevents SQL injection through parameterized queries. `to_dict()` methods standardize JSON serialization.

### Data Storage Solutions

**Primary Database:**
- SQLite (development): File-based at `pricepulse.db`
- MySQL (production): Connection via `mysql+pymysql://` URI pattern
- Configuration via environment variables for deployment flexibility

**Schema Design:**
- Products table with composite e-commerce data (both platforms)
- Brand field auto-extracted from product names using keyword matching
- Coupon support fields for promotional offers
- Timestamp tracking (created_at, updated_at) with automatic updates
- Cascading deletes for price_history relationship

**Migration Strategy:**
- Flask-SQLAlchemy `db.create_all()` for initial schema
- Manual migration script (`migrations_add_columns.py`) demonstrates column addition pattern
- Schema changes can be version-controlled through migration files

### External Dependencies

**Web Scraping Services:**
- **Selenium WebDriver**: Headless Chrome automation for JavaScript-rendered pages
- **BeautifulSoup4**: HTML parsing for extracting product data
- **Requests**: HTTP client for static page scraping
- Custom `HttpClient` service with user-agent rotation, proxy support, and rate limiting

**Third-Party Integrations:**
- **Amazon Product Advertising API**: Optional adapter for product search (`services/api_integrations.py`)
- **Flipkart Affiliate API**: Optional adapter for product data
- Fallback to scraping when API keys unavailable

**Data Import/Export:**
- CSV import functionality (`import_csv.py`) for bulk product loading
- Brand extraction algorithm supporting 30+ consumer electronics brands
- Export capability for database backups

**Development Dependencies:**
- Flask-CORS for local development API access
- python-dotenv for environment variable management
- Bootstrap CDN and Font Awesome CDN for frontend assets

**Deployment Considerations:**
- Environment-based configuration (development vs production)
- Support for proxy lists in scraping to avoid rate limits
- Configurable scraping intervals and retry logic
- Session management with configurable secret keys
- CORS configuration for production domain restrictions