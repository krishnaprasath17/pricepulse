import logging
import time
import re
from typing import Optional, Dict, List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonScraper:
    def __init__(self):
        self.base_url = "https://www.amazon.in"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def setup_driver(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium Chrome driver started")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return None
    
    def get_product_price(self, url: str) -> Optional[float]:
        driver = self.setup_driver()
        if not driver:
            return None
        
        try:
            driver.get(url)
            time.sleep(2)
            
            price_selectors = [
                'span.a-price-whole',
                'span.a-price span.a-offscreen',
                '.a-price .a-offscreen'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.replace('₹', '').replace(',', '').strip()
                    price_match = re.search(r'(\d+)', price_text)
                    if price_match:
                        return float(price_match.group(1))
                except NoSuchElementException:
                    continue
            
            logger.warning(f"Could not find price for Amazon URL: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error scraping Amazon price: {e}")
            return None
        finally:
            driver.quit()
    
    def search_product(self, query: str, max_results: int = 5) -> List[Dict]:
        driver = self.setup_driver()
        if not driver:
            return []
        
        try:
            search_url = f"{self.base_url}/s?k={query.replace(' ', '+')}"
            driver.get(search_url)
            time.sleep(2)
            
            products = []
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for container in product_containers[:max_results]:
                try:
                    title_elem = container.select_one('h2 a span')
                    price_elem = container.select_one('span.a-price span.a-offscreen')
                    link_elem = container.select_one('h2 a')
                    
                    if title_elem and price_elem and link_elem:
                        title = title_elem.text.strip()
                        price_text = price_elem.text.replace('₹', '').replace(',', '').strip()
                        price = float(price_text) if price_text else 0
                        url = urljoin(self.base_url, link_elem['href'])
                        
                        products.append({
                            'title': title,
                            'price': price,
                            'url': url,
                            'platform': 'Amazon'
                        })
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching Amazon: {e}")
            return []
        finally:
            driver.quit()

class FlipkartScraper:
    def __init__(self):
        self.base_url = "https://www.flipkart.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def setup_driver(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium Chrome driver started for Flipkart")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return None
    
    def get_product_price(self, url: str) -> Optional[float]:
        driver = self.setup_driver()
        if not driver:
            return None
        
        try:
            driver.get(url)
            time.sleep(3)
            
            try:
                close_button = driver.find_element(By.CSS_SELECTOR, 'button._2KpZ6l._2doB4z')
                close_button.click()
                time.sleep(1)
            except:
                pass
            
            price_selectors = [
                'div._30jeq3._16Jk6d',
                'div._30jeq3',
                'div._16Jk6d'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.replace('₹', '').replace(',', '').strip()
                    price_match = re.search(r'(\d+)', price_text)
                    if price_match:
                        return float(price_match.group(1))
                except NoSuchElementException:
                    continue
            
            logger.warning(f"Could not find price for Flipkart URL: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error scraping Flipkart price: {e}")
            return None
        finally:
            driver.quit()
    
    def search_product(self, query: str, max_results: int = 5) -> List[Dict]:
        driver = self.setup_driver()
        if not driver:
            return []
        
        try:
            search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
            driver.get(search_url)
            time.sleep(3)
            
            try:
                close_button = driver.find_element(By.CSS_SELECTOR, 'button._2KpZ6l._2doB4z')
                close_button.click()
                time.sleep(1)
            except:
                pass
            
            products = []
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            product_containers = soup.find_all('div', {'class': '_1AtVbE'})
            
            for container in product_containers[:max_results]:
                try:
                    title_elem = container.select_one('div._4rR01T, a._1fQZEK')
                    price_elem = container.select_one('div._30jeq3')
                    link_elem = container.select_one('a._1fQZEK')
                    
                    if title_elem and price_elem and link_elem:
                        title = title_elem.text.strip()
                        price_text = price_elem.text.replace('₹', '').replace(',', '').strip()
                        price = float(price_text) if price_text else 0
                        url = urljoin(self.base_url, link_elem['href'])
                        
                        products.append({
                            'title': title,
                            'price': price,
                            'url': url,
                            'platform': 'Flipkart'
                        })
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching Flipkart: {e}")
            return []
        finally:
            driver.quit()

class PriceComparisonScraper:
    def __init__(self):
        self.amazon_scraper = AmazonScraper()
        self.flipkart_scraper = FlipkartScraper()
    
    def get_price_comparison(self, amazon_url: Optional[str], flipkart_url: Optional[str]) -> Dict:
        amazon_price = None
        flipkart_price = None
        
        if amazon_url:
            amazon_price = self.amazon_scraper.get_product_price(amazon_url)
            time.sleep(2)
        
        if flipkart_url:
            flipkart_price = self.flipkart_scraper.get_product_price(flipkart_url)
        
        return {
            'amazon_price': amazon_price,
            'flipkart_price': flipkart_price
        }
    
    def search_products(self, query: str, max_results_per_platform: int = 5) -> Dict:
        amazon_results = self.amazon_scraper.search_product(query, max_results_per_platform)
        time.sleep(2)
        flipkart_results = self.flipkart_scraper.search_product(query, max_results_per_platform)
        
        return {
            'amazon': amazon_results,
            'flipkart': flipkart_results
        }
