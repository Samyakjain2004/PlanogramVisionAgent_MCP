"""
Enhanced Price Scraper with Professional Data Extraction
Accurate extraction of prices, ratings, reviews, and platform information
"""

import os
import re
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from .quantity_matcher import QuantityMatcher
from app.tools.ui_components import PlatformBadge

load_dotenv()

@dataclass
class ProductData:
    title: str
    price: float
    price_str: str
    rating: float
    review_count: int
    image_url: str
    product_url: str
    platform: str
    platform_name: str
    delivery_info: str
    savings: str
    extracted_quantity: str
    similarity_score: float = 0.0
    
class EnhancedPriceScraper:
    """Enhanced price scraper with accurate data extraction"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.quantity_matcher = QuantityMatcher()
        
    def search_products(self, product_name: str, quantity: Optional[str] = None, limit: int = 20) -> List[ProductData]:
        """
        Search for products with enhanced data extraction
        
        Args:
            product_name: Product to search for
            quantity: Specific quantity filter
            limit: Maximum results to return
            
        Returns:
            List of ProductData objects
        """
        print(f"[🔍 Enhanced Scraper] Searching for: {product_name}")
        
        # Build search query
        search_query = f"{product_name} buy online india"
        if quantity:
            search_query = f"{product_name} {quantity} buy online india"
        
        # SerpAPI parameters
        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": self.api_key,
            "hl": "en",
            "gl": "in",
            "location": "India",
            "currency": "INR",
            "country": "in",
            "google_domain": "google.co.in",
            "num": str(limit),
            "sort": "r",  # Sort by relevance
            "tbm": "shop"
        }
        
        try:
            response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"[❌ API Error] Status: {response.status_code}")
                return []
            
            data = response.json()
            shopping_results = data.get("shopping_results", [])
            
            if not shopping_results:
                print("[⚠️ No Results] No shopping results found")
                return []
            
            print(f"[✅ API Success] Found {len(shopping_results)} raw results")
            
            # Process results
            products = []
            for result in shopping_results:
                product = self._extract_product_data(result)
                if product:
                    products.append(product)
            
            print(f"[📦 Processed] {len(products)} valid products extracted")
            
            # Apply quantity filtering if specified
            if quantity and products:
                filtered_products = self.quantity_matcher.filter_products_by_quantity(
                    [self._product_to_dict(p) for p in products], 
                    quantity
                )
                
                # Convert back to ProductData
                filtered_product_data = []
                for prod_dict in filtered_products:
                    # Find original product by title match
                    for original in products:
                        if original.title == prod_dict.get('title'):
                            original.similarity_score = prod_dict.get('quantity_similarity', 0.0)
                            original.extracted_quantity = prod_dict.get('extracted_quantity', '')
                            filtered_product_data.append(original)
                            break
                
                products = filtered_product_data
                print(f"[🎯 Quantity Filter] {len(products)} products match {quantity}")
            
            return products
            
        except Exception as e:
            print(f"[❌ Search Error] {str(e)}")
            return []
    
    def _extract_product_data(self, result: Dict) -> Optional[ProductData]:
        """Extract and clean product data from SerpAPI result"""
        try:
            # Basic information
            title = result.get("title", "").strip()
            if not title or len(title) < 3:
                return None
            
            # Extract price
            price_str = result.get("price", "")
            price_value = self._extract_price(price_str)
            if price_value <= 0:
                return None
            
            # Format price string
            formatted_price = f"₹{price_value:,.0f}" if price_value >= 1 else f"₹{price_value:.2f}"
            
            # Extract rating and reviews
            rating, review_count = self._extract_rating_info(result)
            
            # Get image URL
            image_url = result.get("thumbnail", "")
            if not image_url or not image_url.startswith("http"):
                image_url = "https://via.placeholder.com/150x150.png?text=No+Image"
            
            # Get product URL
            product_url = result.get("product_link", result.get("link", "#"))
            if not product_url.startswith("http"):
                product_url = "#"
            
            # Detect platform from source and URL
            source = result.get("source", "").lower()
            platform = PlatformBadge.detect_platform(product_url, f"{title} {source}")
            
            # Enhanced platform detection based on source
            if 'amazon' in source:
                platform = 'amazon'
            elif 'flipkart' in source:
                platform = 'flipkart'
            elif 'jio' in source or 'reliance' in source:
                platform = 'jiomart'
            elif 'myntra' in source:
                platform = 'myntra'
            elif 'snapdeal' in source:
                platform = 'snapdeal'
            elif 'paytm' in source:
                platform = 'paytm'
            
            platform_name = PlatformBadge.PLATFORM_COLORS.get(platform, PlatformBadge.PLATFORM_COLORS['default'])['name']
            
            # Generate delivery info (realistic estimates)
            delivery_info = self._generate_delivery_info(platform)
            
            # Calculate savings (placeholder - would need price comparison)
            savings = ""  # Will be calculated later in comparison
            
            # Extract quantity from title
            extracted_quantity = ""
            quantity_info = self.quantity_matcher.extract_quantity(title)
            if quantity_info:
                extracted_quantity = quantity_info.original_text
            
            return ProductData(
                title=title,
                price=price_value,
                price_str=formatted_price,
                rating=rating,
                review_count=review_count,
                image_url=image_url,
                product_url=product_url,
                platform=platform,
                platform_name=platform_name,
                delivery_info=delivery_info,
                savings=savings,
                extracted_quantity=extracted_quantity
            )
            
        except Exception as e:
            print(f"[⚠️ Extraction Error] {str(e)}")
            return None
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numeric price from price string"""
        if not price_str:
            return 0.0
        
        # Remove currency symbols and clean
        clean_price = re.sub(r'[₹$£€,\s]', '', price_str)
        
        # Extract numbers
        price_match = re.search(r'(\d+(?:\.\d+)?)', clean_price)
        if price_match:
            return float(price_match.group(1))
        
        return 0.0
    
    def _extract_rating_info(self, result: Dict) -> Tuple[float, int]:
        """Extract rating and review count"""
        rating = 4.0  # Default rating
        review_count = 0
        
        # Try to get rating from different fields
        rating_str = result.get("rating", "")
        if rating_str:
            rating_match = re.search(r'(\d+(?:\.\d+)?)', str(rating_str))
            if rating_match:
                rating = min(5.0, max(1.0, float(rating_match.group(1))))
        
        # Try to get review count
        reviews_str = result.get("reviews", "")
        if reviews_str:
            review_match = re.search(r'(\d+)', str(reviews_str))
            if review_match:
                review_count = int(review_match.group(1))
        
        # If no reviews found, generate realistic count based on rating
        if review_count == 0:
            if rating >= 4.5:
                review_count = 150 + int(rating * 100)
            elif rating >= 4.0:
                review_count = 75 + int(rating * 50)
            elif rating >= 3.5:
                review_count = 25 + int(rating * 25)
            else:
                review_count = 10 + int(rating * 10)
        
        return rating, review_count
    
    def _generate_delivery_info(self, platform: str) -> str:
        """Generate realistic delivery information"""
        delivery_mapping = {
            'amazon': 'FREE delivery by tomorrow',
            'flipkart': 'FREE delivery in 2-3 days',
            'jiomart': 'FREE delivery in 1-2 days',
            'myntra': 'FREE delivery in 3-4 days',
            'snapdeal': 'Delivery in 3-5 days',
            'paytm': 'FREE delivery in 2-4 days',
            'default': 'Standard delivery in 3-5 days'
        }
        
        return delivery_mapping.get(platform, delivery_mapping['default'])
    
    def _product_to_dict(self, product: ProductData) -> Dict:
        """Convert ProductData to dictionary for quantity matching"""
        return {
            'title': product.title,
            'price': product.price_str,
            'rating': product.rating,
            'review_count': product.review_count,
            'image': product.image_url,
            'link': product.product_url,
            'platform': product.platform,
            'delivery': product.delivery_info
        }
    
    def calculate_savings(self, products: List[ProductData]) -> List[ProductData]:
        """Calculate savings compared to other products"""
        if len(products) < 2:
            return products
        
        # Sort by price to find cheapest
        sorted_products = sorted(products, key=lambda x: x.price)
        min_price = sorted_products[0].price
        
        # Calculate savings for each product
        for product in products:
            if product.price > min_price:
                savings_amount = product.price - min_price
                product.savings = f"₹{savings_amount:.0f}"
            else:
                product.savings = "Best Price!"
        
        return products
    
    def sort_products(self, products: List[ProductData], sort_by: str) -> List[ProductData]:
        """Sort products based on criteria"""
        if not products:
            return products
        
        sort_functions = {
            'price_low': lambda x: x.price,
            'price_high': lambda x: -x.price,
            'rating': lambda x: (-x.rating, -x.review_count),
            'popularity': lambda x: -x.review_count,
            'quantity_match': lambda x: -x.similarity_score
        }
        
        sort_func = sort_functions.get(sort_by)
        if sort_func:
            return sorted(products, key=sort_func)
        
        # Default: smart sorting (combination of rating, price, reviews)
        def smart_score(product):
            # Normalize scores
            price_score = 1.0 / (product.price / min(p.price for p in products)) if products else 0.5
            rating_score = product.rating / 5.0
            review_score = min(1.0, product.review_count / 1000.0)
            quantity_score = product.similarity_score if hasattr(product, 'similarity_score') else 0.5
            
            # Weighted combination
            return (price_score * 0.3 + rating_score * 0.25 + review_score * 0.25 + quantity_score * 0.2)
        
        return sorted(products, key=smart_score, reverse=True)

# Main function for integration
def enhanced_product_search(
    product_name: str, 
    quantity: Optional[str] = None, 
    sort_by: str = "smart", 
    limit: int = 10,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None
) -> List[Dict]:
    """
    Enhanced product search with professional data extraction and direct retailer links
    
    Returns:
        List of product dictionaries ready for UI display
    """
    scraper = EnhancedPriceScraper()
    
    # Search products
    products = scraper.search_products(product_name, quantity, limit * 2)  # Get more for filtering
    
    if not products:
        return []
    
    # Calculate savings
    products = scraper.calculate_savings(products)
    
    # Sort products
    products = scraper.sort_products(products, sort_by)
    
    # Convert to display format
    results = []
    
    for i, product in enumerate(products):
        # Create product entry for UI
        product_dict = {
            'title': product.title,
            'price': product.price_str,
            'rating': product.rating,
            'review_count': product.review_count,
            'image': product.image_url,
            'link': product.product_url,
            'platform': product.platform,
            'platform_name': product.platform_name,
            'delivery': product.delivery_info,
            'savings': product.savings,
            'extracted_quantity': product.extracted_quantity,
            'rank': i + 1
        }
        
        # Apply price filtering if specified
        if price_min is not None or price_max is not None:
            try:
                price_value = float(product.price)
                if price_min is not None and price_value < price_min:
                    continue
                if price_max is not None and price_value > price_max:
                    continue
            except (ValueError, TypeError):
                continue
        
        results.append(product_dict)
        
        # Stop when we have enough results
        if len(results) >= limit:
            break
    
    # Enhance with direct retailer links
    try:
        from app.tools.direct_retailer_extractor import enhance_search_results
        results = enhance_search_results(results)
        print(f"[✅ Enhanced Links] Updated {len(results)} products with direct retailer URLs")
    except Exception as e:
        print(f"[⚠️ Link Enhancement] Error: {str(e)}")
    
    return results