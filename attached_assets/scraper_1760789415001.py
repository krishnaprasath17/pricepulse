"""
Web scraper module for PricePulse
Supports scraping prices from Amazon and Flipkart using BeautifulSoup, Requests, and Selenium
"""

import os
import time
import re
from urllib.parse import urljoin, urlparse
import logging
from typing import Dict, Optional, Tuple, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

# use the project's resilient HttpClient
from services.http_client import HttpClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PriceScraper:
    """Base price scraper class using project's HttpClient.

    This moves request logic to `services.http_client.HttpClient` which
    supports rotating UAs, proxies and throttling.
    """

    def __init__(self, proxies: Optional[List[str]] = None, min_interval_seconds: float = 1.0, timeout: int = 15):
        self.client = HttpClient(proxies=proxies or [], min_interval_seconds=min_interval_seconds, timeout=timeout)
        # default user-agent used by Selenium driver setup when needed
        self.selenium_user_agent = None

    def setup_selenium_driver(self, headless=True):
        """Setup Selenium Chrome driver with a matching user-agent."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        if self.selenium_user_agent:
            chrome_options.add_argument(f'--user-agent={self.selenium_user_agent}')

        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium Chrome driver started")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return None

    def _fetch_url(self, url: str, use_selenium_on_block: bool = True) -> Optional[bytes]:
        """Fetch a URL using HttpClient. If blocked (503/403/captcha) optionally try Selenium.

        Returns raw bytes or None on failure.
        """
        # Allow forcing Selenium for all requests (useful for local testing/debug)
        if os.environ.get('FORCE_SELENIUM') == '1':
            driver = self.setup_selenium_driver(headless=True)
            if driver:
                try:
                    driver.get(url)
                    WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    try:
                        title = driver.title
                        logger.info(f"Selenium loaded page title: {title}")
                    except Exception:
                        pass
                    page = driver.page_source
                    return page.encode('utf-8')
                except Exception as e:
                    logger.error(f"Forced Selenium fetch failed for {url}: {e}")
                finally:
                    try:
                        driver.quit()
                    except Exception:
                        pass
            # fall through to HttpClient if Selenium not available
        try:
            resp = self.client.get(url)
            text = resp.text if hasattr(resp, 'text') else ''
            # Basic blocking detection
            if resp.status_code in (403, 429, 503) or 'captcha' in text.lower() or len(resp.content or b'') < 200:
                logger.info(f"Detected possible bot blocking for {url} (status={resp.status_code}).")
                if use_selenium_on_block:
                    driver = self.setup_selenium_driver(headless=True)
                    if driver:
                        try:
                            driver.get(url)
                            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                            page = driver.page_source
                            return page.encode('utf-8')
                        except Exception as e:
                            logger.error(f"Selenium fallback failed for {url}: {e}")
                        finally:
                            try:
                                driver.quit()
                            except Exception:
                                pass
                return None
            return resp.content
        except Exception as e:
            logger.error(f"HTTP fetch error for {url}: {e}")
            return None

class AmazonScraper(PriceScraper):
    """Amazon price scraper"""
    
    def __init__(self):
        # allow configuring proxies via ROTATING_PROXIES env var (comma-separated)
        proxies = None
        raw = os.environ.get('ROTATING_PROXIES')
        if raw:
            proxies = [p.strip() for p in raw.split(',') if p.strip()]

        super().__init__(proxies=proxies)
        self.base_url = "https://www.amazon.in"
        
    def search_product(self, query: str, max_results: int = 10) -> list:
        """Search for products on Amazon"""
        try:
            search_url = f"{self.base_url}/s?k={query.replace(' ', '+')}"
            content = self._fetch_url(search_url)
            if not content:
                return []
            soup = BeautifulSoup(content, 'html.parser')
            products = []
            
            # Find product containers
            product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
            logger.info(f"Amazon: found {len(product_containers)} result containers for query '{query}'")
            
            parsed = 0
            for idx, container in enumerate(product_containers):
                if parsed >= max_results:
                    break
                try:
                    # Try a variety of ways to locate the title/link — Amazon markup varies.
                    link_elem = None

                    # Common: h2 > a (title anchor). Also try known amazon link classes.
                    candidates = [
                        container.select_one('h2 a'),
                        container.select_one('a.a-link-normal.s-no-outline'),
                        container.select_one('a.a-link-normal.s-underline-text'),
                        container.select_one('a.a-link-normal.a-text-normal'),
                        container.select_one('a.a-link-normal')
                    ]
                    for c in candidates:
                        if c:
                            link_elem = c
                            break

                    # If still nothing, try to find an anchor that points to a product (contains /dp/ or /gp/)
                    if not link_elem:
                        for a in container.find_all('a', href=True):
                            href = a.get('href', '')
                            if '/dp/' in href or '/gp/' in href or '/product/' in href:
                                link_elem = a
                                break

                    # As a last resort, pick any anchor that has text
                    if not link_elem:
                        for a in container.find_all('a', href=True):
                            txt = a.get_text(strip=True)
                            if txt and len(txt) > 3:
                                link_elem = a
                                break

                    if not link_elem:
                        logger.debug(f"Amazon: container {idx} skipped - no link element (containersize={len(container.text or '')})")
                        continue

                    # Try to extract title from common title spans first, then fallback to link text
                    title = None
                    title_selectors = [
                        'span.a-size-medium.a-color-base.a-text-normal',
                        'span.a-size-base-plus.a-color-base.a-text-normal',
                        'span.a-size-medium',
                        'span.a-size-base-plus',
                        'h2',
                    ]
                    for sel in title_selectors:
                        tnode = container.select_one(sel)
                        if tnode and tnode.get_text(strip=True):
                            title = tnode.get_text(strip=True)
                            break

                    if not title:
                        # fallback: use link text
                        title = link_elem.get_text(strip=True)

                    if not title:
                        # diagnostic: log href to help tune selectors
                        href_dbg = link_elem.get('href') or '<no-href>'
                        logger.debug(f"Amazon: container {idx} skipped - no title (link href={href_dbg})")
                        continue

                    # URL
                    href = link_elem.get('href')
                    if not href:
                        logger.debug(f"Amazon: container {idx} skipped - no href (title present)")
                        continue
                    product_url = urljoin(self.base_url, href)

                    # Price: try common selectors including the offscreen full price and nested price spans
                    price_elem = None
                    price_selectors = [
                        'span.a-price > span.a-offscreen',
                        'span.a-offscreen',
                        'span.a-price-whole',
                        'span.a-price',
                        'span.a-size-base.a-color-price',
                        'span.a-price-fraction'
                    ]
                    for ps in price_selectors:
                        pe = container.select_one(ps)
                        if pe and pe.get_text(strip=True):
                            price_elem = pe
                            break

                    if not price_elem:
                        logger.debug(f"Amazon: container {idx} skipped - no price element (href={href})")
                        continue
                    price_text = price_elem.get_text(strip=True).replace('₹', '').replace(',', '')
                    price_match = re.search(r'(\d+[\d,]*)', price_text)
                    if not price_match:
                        logger.debug(f"Amazon: container {idx} skipped - price parse failed (text='{price_text}')")
                        continue
                    price = float(re.sub(r'[^0-9]', '', price_match.group(1)))

                    # Image (best-effort)
                    img_elem = container.select_one('img.s-image') or container.select_one('img')
                    image = img_elem.get('src') if img_elem and img_elem.get('src') else None

                    products.append({
                        'title': title,
                        'price': price,
                        'url': product_url,
                        'image': image,
                        'brand': None,
                        'platform': 'Amazon',
                        'category': None,
                        'source': 'scraper'
                    })
                    parsed += 1

                except Exception as e:
                    logger.warning(f"Error parsing product container idx={idx}: {e}")
                    continue
            logger.info(f"Amazon: parsed {parsed} product(s) for query '{query}'")
            return products
            
        except Exception as e:
            logger.error(f"Error searching Amazon: {e}")
            return []
    
    def get_product_price(self, url: str) -> Optional[float]:
        """Get current price for a specific Amazon product"""
        try:
            content = self._fetch_url(url)
            if not content:
                return None
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try different price selectors
            price_selectors = [
                'span.a-price-whole',
                'span.a-price.a-text-price.a-size-medium.apexPriceToPay',
                'span.a-price.a-text-price.a-size-base.apexPriceToPay',
                'span.a-price.a-text-price'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True).replace(',', '')
                    price_match = re.search(r'(\d+)', price_text)
                    if price_match:
                        return float(price_match.group(1))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Amazon price from {url}: {e}")
            return None

class FlipkartScraper(PriceScraper):
    """Flipkart price scraper"""
    
    def __init__(self):
        proxies = None
        raw = os.environ.get('ROTATING_PROXIES')
        if raw:
            proxies = [p.strip() for p in raw.split(',') if p.strip()]

        super().__init__(proxies=proxies)
        self.base_url = "https://www.flipkart.com"
        
    def search_product(self, query: str, max_results: int = 10) -> list:
        """Search for products on Flipkart"""
        try:
            search_url = f"{self.base_url}/search?q={query.replace(' ', '%20')}"
            content = self._fetch_url(search_url)
            if not content:
                return []
            soup = BeautifulSoup(content, 'html.parser')
            products = []
            
            # Find product containers
            product_containers = soup.find_all('div', class_='_1AtVbE')

            for container in product_containers[:max_results*2]:
                try:
                    # Flipkart has multiple layouts. Try the modern list view first
                    a_full = container.select_one('a._1fQZEK')
                    if a_full:
                        title_elem = a_full.select_one('div._4rR01T')
                        price_elem = a_full.select_one('div._30jeq3')
                        href = a_full.get('href')
                        title = title_elem.get_text(strip=True) if title_elem else a_full.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True).replace('₹', '').replace(',', '') if price_elem else None
                        url = urljoin(self.base_url, href) if href else None
                        img_elem = a_full.select_one('img')
                    else:
                        # Grid / alternate layout
                        a_grid = container.select_one('a.s1Q9rs') or container.select_one('a.IRpwTa')
                        if not a_grid:
                            continue
                        title = a_grid.get_text(strip=True)
                        href = a_grid.get('href')
                        price_elem = container.select_one('div._30jeq3')
                        price_text = price_elem.get_text(strip=True).replace('₹', '').replace(',', '') if price_elem else None
                        url = urljoin(self.base_url, href) if href else None
                        img_elem = container.select_one('img')

                    if not price_text or not url:
                        continue

                    price_match = re.search(r'(\d+[\d,]*)', price_text)
                    if not price_match:
                        continue
                    price = float(re.sub(r'[^0-9]', '', price_match.group(1)))

                    image = img_elem.get('src') if img_elem and img_elem.get('src') else None

                    products.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'image': image,
                        'brand': None,
                        'platform': 'Flipkart',
                        'category': None,
                        'source': 'scraper'
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing product container: {e}")
                    continue
                    
            return products
            
        except Exception as e:
            logger.error(f"Error searching Flipkart: {e}")
            return []
    
    def get_product_price(self, url: str) -> Optional[float]:
        """Get current price for a specific Flipkart product"""
        try:
            content = self._fetch_url(url)
            if not content:
                return None
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try different price selectors
            price_selectors = [
                'div._30jeq3._16Jk6d',
                'div._30jeq3',
                'span._30jeq3._16Jk6d'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True).replace('₹', '').replace(',', '')
                    price_match = re.search(r'(\d+)', price_text)
                    if price_match:
                        return float(price_match.group(1))
            
            return None
        except Exception as e:
            logger.error(f"Error getting Flipkart price from {url}: {e}")


def scrape_flipkart_simple(product_name: str) -> str:
    """Simple Flipkart search that returns the first price string or an error message.

    This helper is intentionally lightweight and best-effort — for robust scraping use FlipkartScraper class.
    """
    try:
        query = product_name.replace(' ', '%20')
        url = f'https://www.flipkart.com/search?q={query}'
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        price_elem = soup.select_one('div._30jeq3')
        if price_elem:
            return price_elem.get_text(strip=True)
        return 'Flipkart: Price not found'
    except Exception as e:
        logger.debug(f"scrape_flipkart_simple error: {e}")
        return f'Flipkart: error ({e})'


def scrape_amazon_simple(product_name: str) -> str:
    """Simple Amazon search using Selenium to render JS; returns first found price string or message.

    Note: Requires ChromeDriver on PATH and Chrome installed. Use AmazonScraper for production use.
    """
    scraper = PriceScraper()
    driver = scraper.setup_selenium_driver(headless=True)
    if not driver:
        return 'Amazon: Selenium driver not available'
    try:
        search_url = f'https://www.amazon.in/s?k={product_name.replace(" ", "+")}'
        driver.get(search_url)
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        price_elem = soup.select_one('.a-price .a-offscreen')
        if price_elem:
            return price_elem.get_text(strip=True)
        return 'Amazon: Price not found'
    except Exception as e:
        logger.debug(f"scrape_amazon_simple error: {e}")
        return f'Amazon: error ({e})'
    finally:
        try:
            driver.quit()
        except Exception:
            pass
            return None


# Smartprix support removed — only Amazon and Flipkart are used now.

class PriceComparisonScraper:
    """Main scraper class that combines Amazon and Flipkart scraping"""
    
    def __init__(self):
        self.amazon_scraper = AmazonScraper()
        self.flipkart_scraper = FlipkartScraper()
        # no third-party scraper; using only Amazon and Flipkart
        self.smartprix_scraper = None

        # default categories we support
        self.supported_categories = ['laptops', 'phones', 'headphones']

    def _normalize_and_tag(self, item: dict, category: Optional[str], platform: str) -> dict:
        """Ensure a consistent schema for scraped items and tag with category/platform."""
        normalized = {
            'title': item.get('title') or item.get('product_name') or item.get('name'),
            'price': item.get('price'),
            'url': item.get('url'),
            'image': item.get('image'),
            'brand': item.get('brand'),
            'platform': platform,
            'category': category,
            'source': item.get('source', 'scraper')
        }
        return normalized

    def scrape_category(self, category: str, max_per_platform: int = 10) -> List[dict]:
        """Scrape a given category (laptops, phones, headphones) across platforms."""
        if category not in self.supported_categories:
            raise ValueError(f"Unsupported category: {category}")

        queries = {
            'laptops': ['laptop', 'notebook'],
            'phones': ['smartphone', 'mobile phone', 'phone'],
            'headphones': ['headphones', 'earbuds', 'earphones']
        }

        qlist = queries.get(category, [category])
        results: List[dict] = []

        for q in qlist:
            # Amazon
            try:
                amazon_items = self.amazon_scraper.search_product(q, max_results=max_per_platform)
                for it in amazon_items:
                    results.append(self._normalize_and_tag(it, category, 'amazon'))
            except Exception as e:
                logger.warning(f"Amazon search for '{q}' failed: {e}")

            # Flipkart
            try:
                fk_items = self.flipkart_scraper.search_product(q, max_results=max_per_platform)
                for it in fk_items:
                    results.append(self._normalize_and_tag(it, category, 'flipkart'))
            except Exception as e:
                logger.warning(f"Flipkart search for '{q}' failed: {e}")

            # no smartprix scraping

            # brief delay between different query iterations
            time.sleep(0.5)

        return results

    def scrape_categories(self, categories: Optional[List[str]] = None, max_per_platform: int = 8) -> List[dict]:
        """Scrape multiple categories and return aggregate list."""
        categories = categories or self.supported_categories
        all_results: List[dict] = []
        for c in categories:
            all_results.extend(self.scrape_category(c, max_per_platform=max_per_platform))
        return all_results

    def export_to_csv(self, items: List[dict], path: str) -> None:
        """Write results to CSV with normalized columns."""
        import csv
        fieldnames = ['title', 'price', 'url', 'image', 'brand', 'platform', 'category', 'source']
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for it in items:
                writer.writerow({k: it.get(k) for k in fieldnames})
        
    def search_products(self, query: str, max_results_per_platform: int = 5) -> Dict[str, list]:
        """Search for products on both platforms"""
        amazon_results = self.amazon_scraper.search_product(query, max_results_per_platform)
        flipkart_results = self.flipkart_scraper.search_product(query, max_results_per_platform)
        smartprix_results = []
        if getattr(self, 'smartprix_scraper', None):
            smartprix_results = self.smartprix_scraper.search_product(query, max_results_per_platform)
        
        return {
            'amazon': amazon_results,
            'flipkart': flipkart_results
            , 'smartprix': smartprix_results
        }
    
    def get_price_comparison(self, amazon_url: str, flipkart_url: str) -> Dict[str, Optional[float]]:
        """Get price comparison for specific product URLs"""
        amazon_price = self.amazon_scraper.get_product_price(amazon_url)
        flipkart_price = self.flipkart_scraper.get_product_price(flipkart_url)
        
        return {
            'amazon_price': amazon_price,
            'flipkart_price': flipkart_price,
            'best_price': min(filter(None, [amazon_price, flipkart_price])) if any([amazon_price, flipkart_price]) else None
        }
    
    def update_product_prices(self, products: list) -> list:
        """Update prices for a list of products"""
        updated_products = []
        
        for product in products:
            try:
                amazon_price = None
                flipkart_price = None
                
                if product.get('amazon_url'):
                    amazon_price = self.amazon_scraper.get_product_price(product['amazon_url'])
                
                if product.get('flipkart_url'):
                    flipkart_price = self.flipkart_scraper.get_product_price(product['flipkart_url'])
                
                updated_product = product.copy()
                updated_product['amazon_price'] = amazon_price
                updated_product['flipkart_price'] = flipkart_price
                updated_product['last_updated'] = time.time()
                
                updated_products.append(updated_product)
                
                # Add delay to avoid being blocked
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error updating product {product.get('product_name', 'Unknown')}: {e}")
                updated_products.append(product)
        
        return updated_products

def main():
    """Example usage of the scraper"""
    scraper = PriceComparisonScraper()

    # Scrape three categories and export to CSV (dry-run)
    cats = ['laptops', 'phones', 'headphones']
    aggregated = scraper.scrape_categories(categories=cats, max_per_platform=5)

    print(f"Scraped {len(aggregated)} items across categories: {', '.join(cats)}")
    # show a few samples
    for i, item in enumerate(aggregated[:10]):
        print(f"{i+1}. [{item['platform']}/{item['category']}] {item['title']} - {item.get('price')}")

    # optional: save to CSV in current folder
    out = os.path.join(os.getcwd(), 'scraped_products.csv')
    try:
        scraper.export_to_csv(aggregated, out)
        print(f"Exported CSV to: {out}")
    except Exception as e:
        logger.warning(f"Failed to export CSV: {e}")

if __name__ == "__main__":
    main()
