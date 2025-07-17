#!/usr/bin/env python3
"""
Direct Retailer URL Extractor
Extracts actual retailer URLs from SerpAPI results and bypasses Google Shopping
"""

import requests
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, unquote
import time

class DirectRetailerExtractor:
    """Extract direct retailer URLs from search results"""
    
    # Top 20 trusted e-commerce platforms in India
    TRUSTED_RETAILERS = {
        'amazon.in': {
            'name': 'Amazon India',
            'color': '#FF9900',
            'trust_score': 10,
            'delivery_info': 'FREE delivery by tomorrow'
        },
        'flipkart.com': {
            'name': 'Flipkart',
            'color': '#2874F0', 
            'trust_score': 10,
            'delivery_info': 'FREE delivery in 2-3 days'
        },
        'myntra.com': {
            'name': 'Myntra',
            'color': '#FF3E6C',
            'trust_score': 9,
            'delivery_info': 'FREE delivery in 3-5 days'
        },
        'bigbasket.com': {
            'name': 'BigBasket',
            'color': '#84C341',
            'trust_score': 9,
            'delivery_info': 'Same day delivery available'
        },
        'jiomart.com': {
            'name': 'JioMart',
            'color': '#008ECC',
            'trust_score': 8,
            'delivery_info': 'FREE delivery in 2-4 days'
        },
        'nykaa.com': {
            'name': 'Nykaa',
            'color': '#FC2779',
            'trust_score': 9,
            'delivery_info': 'FREE delivery in 3-5 days'
        },
        'snapdeal.com': {
            'name': 'Snapdeal',
            'color': '#E53E3E',
            'trust_score': 7,
            'delivery_info': 'Standard delivery in 4-6 days'
        },
        'paytmmall.com': {
            'name': 'Paytm Mall',
            'color': '#00BAF2',
            'trust_score': 7,
            'delivery_info': 'Standard delivery in 3-5 days'
        },
        'tatacliq.com': {
            'name': 'Tata CLiQ',
            'color': '#019CDB',
            'trust_score': 8,
            'delivery_info': 'FREE delivery in 2-4 days'
        },
        'shopclues.com': {
            'name': 'ShopClues',
            'color': '#FF6B35',
            'trust_score': 6,
            'delivery_info': 'Standard delivery in 5-7 days'
        },
        'grofers.com': {
            'name': 'Blinkit (Grofers)',
            'color': '#FCDC00',
            'trust_score': 8,
            'delivery_info': 'Delivery in 15-30 minutes'
        },
        'zepto.com': {
            'name': 'Zepto',
            'color': '#6C5CE7',
            'trust_score': 8,
            'delivery_info': 'Delivery in 10 minutes'
        },
        'reliance.com': {
            'name': 'Reliance Digital',
            'color': '#1976D2',
            'trust_score': 8,
            'delivery_info': 'Standard delivery in 3-5 days'
        },
        'croma.com': {
            'name': 'Croma',
            'color': '#7B68EE',
            'trust_score': 8,
            'delivery_info': 'Standard delivery in 3-5 days'
        },
        'vijaysales.com': {
            'name': 'Vijay Sales',
            'color': '#FF6B00',
            'trust_score': 7,
            'delivery_info': 'Standard delivery in 4-6 days'
        },
        'lenskart.com': {
            'name': 'Lenskart',
            'color': '#0DB7C4',
            'trust_score': 9,
            'delivery_info': 'FREE delivery in 3-5 days'
        },
        'pharmeasy.in': {
            'name': 'PharmEasy',
            'color': '#06C270',
            'trust_score': 9,
            'delivery_info': 'Same day delivery for medicines'
        },
        'netmeds.com': {
            'name': 'Netmeds',
            'color': '#00A99D',
            'trust_score': 8,
            'delivery_info': 'Express delivery in 2-4 hours'
        },
        'firstcry.com': {
            'name': 'FirstCry',
            'color': '#FFA500',
            'trust_score': 8,
            'delivery_info': 'FREE delivery in 3-5 days'
        },
        'purplle.com': {
            'name': 'Purplle',
            'color': '#7C4DFF',
            'trust_score': 7,
            'delivery_info': 'FREE delivery in 4-6 days'
        }
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_direct_url(self, google_shopping_url: str) -> Tuple[str, str, Dict]:
        """
        Extract direct retailer URL from Google Shopping URL
        
        Args:
            google_shopping_url: Google Shopping product URL
            
        Returns:
            Tuple of (direct_url, retailer_name, retailer_info)
        """
        try:
            # Check if it's already a direct URL
            direct_retailer = self._identify_direct_retailer(google_shopping_url)
            if direct_retailer:
                retailer_info = self.TRUSTED_RETAILERS.get(direct_retailer, {})
                return google_shopping_url, retailer_info.get('name', direct_retailer), retailer_info
            
            # If it's a Google Shopping URL, try to extract the actual retailer URL
            if 'google.co' in google_shopping_url and 'shopping' in google_shopping_url:
                return self._resolve_google_shopping_url(google_shopping_url)
            
            # Try to resolve any redirects
            return self._resolve_redirects(google_shopping_url)
            
        except Exception as e:
            print(f"❌ Error extracting direct URL: {str(e)}")
            return google_shopping_url, "Unknown Store", {}
    
    def _identify_direct_retailer(self, url: str) -> Optional[str]:
        """Identify if URL is from a trusted retailer"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check exact matches first
            if domain in self.TRUSTED_RETAILERS:
                return domain
            
            # Check for subdomain matches
            for retailer in self.TRUSTED_RETAILERS:
                if retailer in domain:
                    return retailer
            
            return None
            
        except Exception:
            return None
    
    def _resolve_google_shopping_url(self, google_url: str) -> Tuple[str, str, Dict]:
        """Resolve Google Shopping URL to actual retailer"""
        try:
            # Parse the Google Shopping URL to extract product info
            parsed = urlparse(google_url)
            
            # Try to find merchant information in the URL parameters
            if 'merchant' in google_url or 'ved' in google_url:
                # Make a HEAD request to get redirects
                response = self.session.head(google_url, allow_redirects=True, timeout=5)
                
                final_url = response.url
                direct_retailer = self._identify_direct_retailer(final_url)
                
                if direct_retailer:
                    retailer_info = self.TRUSTED_RETAILERS[direct_retailer]
                    return final_url, retailer_info['name'], retailer_info
            
            # Fallback: try to extract merchant info from URL structure
            retailer_name, retailer_info = self._extract_merchant_from_url(google_url)
            return google_url, retailer_name, retailer_info
            
        except Exception as e:
            print(f"❌ Error resolving Google Shopping URL: {str(e)}")
            return google_url, "Online Store", {}

    def _resolve_redirects(self, url: str) -> Tuple[str, str, Dict]:
        """Resolve URL redirects to find final retailer"""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=5)
            final_url = response.url
            
            direct_retailer = self._identify_direct_retailer(final_url)
            if direct_retailer:
                retailer_info = self.TRUSTED_RETAILERS[direct_retailer]
                return final_url, retailer_info['name'], retailer_info
            
            # If not a known retailer, return as unknown
            domain = urlparse(final_url).netloc
            return final_url, domain, {}
            
        except Exception:
            return url, "Unknown Store", {}
    
    def _extract_merchant_from_url(self, url: str) -> Tuple[str, Dict]:
        """Extract merchant information from URL structure"""
        # Look for merchant names in the URL
        url_lower = url.lower()
        
        for domain, info in self.TRUSTED_RETAILERS.items():
            retailer_name = domain.split('.')[0]  # Get main name (e.g., 'amazon' from 'amazon.in')
            
            if retailer_name in url_lower:
                return info['name'], info

        return "Online Store", {}

    def enhance_product_with_direct_links(self, product_data: Dict) -> Dict:
        """Enhance product data with direct retailer links"""
        try:
            original_url = product_data.get('link', '')
            
            if original_url:
                direct_url, retailer_name, retailer_info = self.extract_direct_url(original_url)
                
                # Update product data
                product_data['link'] = direct_url
                product_data['platform_name'] = retailer_name
                product_data['trust_score'] = retailer_info.get('trust_score', 5)
                
                # Update delivery info based on retailer
                if retailer_info.get('delivery_info'):
                    product_data['delivery'] = retailer_info['delivery_info']
                
                # Update platform for UI components
                domain = urlparse(direct_url).netloc.lower()
                if 'amazon' in domain:
                    product_data['platform'] = 'amazon'
                elif 'flipkart' in domain:
                    product_data['platform'] = 'flipkart'
                elif 'jio' in domain:
                    product_data['platform'] = 'jiomart'
                elif 'myntra' in domain:
                    product_data['platform'] = 'myntra'
                elif 'bigbasket' in domain:
                    product_data['platform'] = 'bigbasket'
                elif 'nykaa' in domain:
                    product_data['platform'] = 'nykaa'
                else:
                    product_data['platform'] = 'default'
            
            return product_data
            
        except Exception as e:
            print(f"❌ Error enhancing product links: {str(e)}")
            return product_data
    
    def get_retailer_info(self, domain: str) -> Dict:
        """Get information about a retailer domain"""
        domain = domain.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return self.TRUSTED_RETAILERS.get(domain, {
            'name': domain,
            'color': '#6C757D',
            'trust_score': 5,
            'delivery_info': 'Standard delivery'
        })
    
    def batch_enhance_products(self, products: List[Dict]) -> List[Dict]:
        """Enhance multiple products with direct links"""
        enhanced_products = []
        
        for product in products:
            enhanced_product = self.enhance_product_with_direct_links(product.copy())
            enhanced_products.append(enhanced_product)
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        # Sort by trust score and price
        enhanced_products.sort(key=lambda x: (
            -x.get('trust_score', 5),  # Higher trust score first
            float(re.sub(r'[^\d.]', '', x.get('price', '999999')))  # Lower price first
        ))
        
        return enhanced_products

# === Integration Functions ===
def enhance_product_links(product_data: Dict) -> Dict:
    """Enhance single product with direct retailer link"""
    extractor = DirectRetailerExtractor()
    return extractor.enhance_product_with_direct_links(product_data)

def enhance_search_results(products: List[Dict]) -> List[Dict]:
    """Enhance search results with direct retailer links"""
    extractor = DirectRetailerExtractor()
    return extractor.batch_enhance_products(products)