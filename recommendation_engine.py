"""
Advanced Recommendation Engine for Price Agent
Handles multi-criteria scoring, product ranking, and intelligent recommendations
"""

import re
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class SortCriteria(Enum):
    PRICE_LOW_TO_HIGH = "price_asc"
    PRICE_HIGH_TO_LOW = "price_desc"
    RATING_HIGH_TO_LOW = "rating_desc"
    REVIEWS_HIGH_TO_LOW = "reviews_desc"
    DELIVERY_FASTEST = "delivery_asc"
    RECOMMENDATION_SCORE = "recommendation_desc"

@dataclass
class ProductMetrics:
    """Structured product metrics for recommendation scoring"""
    title: str
    price: float
    rating: float
    review_count: int
    delivery_days: int
    source: str
    image_url: str
    product_url: str
    quantity: str
    quantity_value: float
    quantity_unit: str
    price_per_unit: float
    
    # Calculated scores
    price_score: float = 0.0
    rating_score: float = 0.0
    review_score: float = 0.0
    delivery_score: float = 0.0
    overall_score: float = 0.0

class QuantityMatcher:
    """Smart quantity detection and matching"""
    
    UNIT_CONVERSIONS = {
        'ml': 1,
        'l': 1000,
        'litre': 1000,
        'liter': 1000,
        'g': 1,
        'gm': 1,
        'gram': 1,
        'kg': 1000,
        'kilogram': 1000,
        'piece': 1,
        'pcs': 1,
        'pack': 1,
        'unit': 1
    }
    
    @staticmethod
    def extract_quantity(title: str) -> Tuple[float, str]:
        """Extract quantity and unit from product title"""
        title_lower = title.lower()
        
        # Common patterns for quantity extraction
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|g|gm|gram|kg|kilogram|piece|pcs|pack|unit)',
            r'(\d+(?:\.\d+)?)\s*(ml|l|g|kg)',
            r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|l|g|kg)',
            r'pack\s*of\s*(\d+)',
            r'(\d+)\s*pieces?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title_lower)
            if match:
                if len(match.groups()) == 2:
                    quantity, unit = match.groups()
                    return float(quantity), unit.lower()
                elif len(match.groups()) == 3:
                    count, quantity, unit = match.groups()
                    return float(count) * float(quantity), unit.lower()
                elif len(match.groups()) == 1:
                    return float(match.group(1)), 'piece'
        
        return 1.0, 'piece'
    
    @staticmethod
    def normalize_quantity(quantity: float, unit: str) -> float:
        """Normalize quantity to base unit for comparison"""
        unit_lower = unit.lower()
        return quantity * QuantityMatcher.UNIT_CONVERSIONS.get(unit_lower, 1)
    
    @staticmethod
    def filter_by_quantity(products: List[Dict], target_quantity: float, target_unit: str, tolerance: float = 0.3) -> List[Dict]:
        """Filter products by quantity with tolerance"""
        target_normalized = QuantityMatcher.normalize_quantity(target_quantity, target_unit)
        
        filtered = []
        for product in products:
            title = product.get('title', '')
            quantity, unit = QuantityMatcher.extract_quantity(title)
            normalized = QuantityMatcher.normalize_quantity(quantity, unit)
            
            # Check if within tolerance range
            if abs(normalized - target_normalized) / target_normalized <= tolerance:
                product['extracted_quantity'] = quantity
                product['extracted_unit'] = unit
                product['normalized_quantity'] = normalized
                filtered.append(product)
        
        return filtered

class RecommendationEngine:
    """Advanced recommendation engine with multi-criteria scoring"""
    
    def __init__(self, weights: Dict[str, float] = None):
        """Initialize with scoring weights"""
        self.weights = weights or {
            'price': 0.35,      # 35% weight for price (lower is better)
            'rating': 0.25,     # 25% weight for rating (higher is better)
            'reviews': 0.20,    # 20% weight for review count (higher is better)
            'delivery': 0.20    # 20% weight for delivery speed (lower is better)
        }
    
    def extract_metrics(self, product: Dict) -> ProductMetrics:
        """Extract structured metrics from product data"""
        title = product.get('title', '')
        price_str = product.get('price', '₹0')
        
        # Extract price
        price_match = re.search(r'[\d,]+(?:\.\d+)?', price_str.replace('₹', '').replace(',', ''))
        price = float(price_match.group()) if price_match else 0.0
        
        # Extract rating (mock data for now, will be enhanced with real data)
        rating = self._mock_rating(title)
        
        # Extract review count (mock data for now)
        review_count = self._mock_review_count(title)
        
        # Extract delivery days (mock data for now)
        delivery_days = self._mock_delivery_days(product.get('source', ''))
        
        # Extract quantity information
        quantity, unit = QuantityMatcher.extract_quantity(title)
        normalized_quantity = QuantityMatcher.normalize_quantity(quantity, unit)
        
        # Calculate price per unit
        price_per_unit = price / normalized_quantity if normalized_quantity > 0 else price
        
        return ProductMetrics(
            title=title,
            price=price,
            rating=rating,
            review_count=review_count,
            delivery_days=delivery_days,
            source=product.get('source', ''),
            image_url=product.get('thumbnail', ''),
            product_url=product.get('product_link', ''),
            quantity=f"{quantity} {unit}",
            quantity_value=quantity,
            quantity_unit=unit,
            price_per_unit=price_per_unit
        )
    
    def calculate_scores(self, products: List[ProductMetrics]) -> List[ProductMetrics]:
        """Calculate normalized scores for all products"""
        if not products:
            return []
        
        # Extract values for normalization
        prices = [p.price for p in products if p.price > 0]
        ratings = [p.rating for p in products]
        reviews = [p.review_count for p in products]
        deliveries = [p.delivery_days for p in products]
        
        # Calculate min/max for normalization
        price_min, price_max = (min(prices), max(prices)) if prices else (0, 1)
        rating_min, rating_max = (min(ratings), max(ratings)) if ratings else (0, 5)
        review_min, review_max = (min(reviews), max(reviews)) if reviews else (0, 100)
        delivery_min, delivery_max = (min(deliveries), max(deliveries)) if deliveries else (1, 7)
        
        # Calculate scores for each product
        for product in products:
            # Price score (lower is better, so invert)
            if price_max > price_min:
                product.price_score = 1 - (product.price - price_min) / (price_max - price_min)
            else:
                product.price_score = 1.0
            
            # Rating score (higher is better)
            if rating_max > rating_min:
                product.rating_score = (product.rating - rating_min) / (rating_max - rating_min)
            else:
                product.rating_score = 1.0
            
            # Review score (higher is better, with logarithmic scaling)
            if review_max > review_min:
                log_reviews = math.log(product.review_count + 1)
                log_max = math.log(review_max + 1)
                product.review_score = log_reviews / log_max
            else:
                product.review_score = 1.0
            
            # Delivery score (lower is better, so invert)
            if delivery_max > delivery_min:
                product.delivery_score = 1 - (product.delivery_days - delivery_min) / (delivery_max - delivery_min)
            else:
                product.delivery_score = 1.0
            
            # Overall weighted score
            product.overall_score = (
                product.price_score * self.weights['price'] +
                product.rating_score * self.weights['rating'] +
                product.review_score * self.weights['reviews'] +
                product.delivery_score * self.weights['delivery']
            )
        
        return products
    
    def rank_products(self, products: List[Dict], sort_by: SortCriteria = SortCriteria.RECOMMENDATION_SCORE, 
                     limit: int = 5) -> List[ProductMetrics]:
        """Rank products based on criteria"""
        # Convert to metrics
        metrics = [self.extract_metrics(p) for p in products]
        
        # Calculate scores
        metrics = self.calculate_scores(metrics)
        
        # Sort based on criteria
        if sort_by == SortCriteria.PRICE_LOW_TO_HIGH:
            metrics.sort(key=lambda x: x.price)
        elif sort_by == SortCriteria.PRICE_HIGH_TO_LOW:
            metrics.sort(key=lambda x: x.price, reverse=True)
        elif sort_by == SortCriteria.RATING_HIGH_TO_LOW:
            metrics.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == SortCriteria.REVIEWS_HIGH_TO_LOW:
            metrics.sort(key=lambda x: x.review_count, reverse=True)
        elif sort_by == SortCriteria.DELIVERY_FASTEST:
            metrics.sort(key=lambda x: x.delivery_days)
        else:  # RECOMMENDATION_SCORE
            metrics.sort(key=lambda x: x.overall_score, reverse=True)
        
        return metrics[:limit]
    
    def _mock_rating(self, title: str) -> float:
        """Mock rating generation (will be replaced with real data)"""
        # Generate consistent rating based on title hash
        hash_val = hash(title) % 100
        return 3.5 + (hash_val / 100) * 1.5  # Range: 3.5 to 5.0
    
    def _mock_review_count(self, title: str) -> int:
        """Mock review count generation (will be replaced with real data)"""
        # Generate consistent review count based on title hash
        hash_val = hash(title) % 1000
        return 10 + hash_val  # Range: 10 to 1010
    
    def _mock_delivery_days(self, source: str) -> int:
        """Mock delivery days based on source (will be replaced with real data)"""
        delivery_map = {
            'amazon': 1,
            'flipkart': 2,
            'myntra': 3,
            'snapdeal': 4,
            'paytm': 3,
            'shopclues': 5,
            'default': 3
        }
        
        source_lower = source.lower()
        for key, days in delivery_map.items():
            if key in source_lower:
                return days
        
        return delivery_map['default']
    
    def generate_recommendation_reasons(self, top_products: List[ProductMetrics]) -> List[str]:
        """Generate reasons for product recommendations"""
        reasons = []
        
        for i, product in enumerate(top_products):
            reason_parts = []
            
            # Price advantage
            if product.price_score > 0.7:
                reason_parts.append("excellent price")
            elif product.price_score > 0.5:
                reason_parts.append("good value")
            
            # Rating advantage
            if product.rating_score > 0.8:
                reason_parts.append("high customer rating")
            elif product.rating_score > 0.6:
                reason_parts.append("good reviews")
            
            # Delivery advantage
            if product.delivery_score > 0.8:
                reason_parts.append("fast delivery")
            elif product.delivery_score > 0.6:
                reason_parts.append("reasonable delivery")
            
            # Review count advantage
            if product.review_score > 0.7:
                reason_parts.append("well-reviewed")
            
            # Construct reason
            if reason_parts:
                reason = f"#{i+1} choice for {', '.join(reason_parts[:2])}"
            else:
                reason = f"#{i+1} balanced option"
            
            reasons.append(reason)
        
        return reasons