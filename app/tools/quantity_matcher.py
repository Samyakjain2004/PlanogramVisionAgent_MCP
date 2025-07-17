"""
Smart Quantity Matching System
Handles quantity normalization, tolerance-based matching, and product filtering
"""

import re
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass

@dataclass
class QuantityInfo:
    value: float
    unit: str
    original_text: str
    normalized_ml: float  # Everything converted to ml for comparison

class QuantityMatcher:
    """Smart quantity matching with tolerance and unit conversion"""
    
    # Unit conversion to ml
    UNIT_CONVERSIONS = {
        'ml': 1,
        'l': 1000,
        'liter': 1000,
        'litre': 1000,
        'g': 1,  # For dry products, treat g as ml equivalent
        'gm': 1,
        'gram': 1,
        'kg': 1000,
        'kilogram': 1000,
        'oz': 29.5735,  # Fluid ounces
        'fl oz': 29.5735,
        'pint': 473.176,
        'quart': 946.353,
        'gallon': 3785.41
    }
    
    # Common product categories and their typical units
    CATEGORY_UNITS = {
        'detergent': ['ml', 'l', 'g', 'kg'],
        'soap': ['g', 'gm', 'piece'],
        'shampoo': ['ml', 'l'],
        'oil': ['ml', 'l'],
        'powder': ['g', 'kg'],
        'liquid': ['ml', 'l']
    }
    
    def __init__(self, tolerance_percentage: float = 20.0):
        """
        Initialize quantity matcher
        
        Args:
            tolerance_percentage: Allowed variance in quantity (default 20%)
        """
        self.tolerance = tolerance_percentage / 100.0
    
    def extract_quantity(self, text: str) -> Optional[QuantityInfo]:
        """
        Extract quantity information from product text
        
        Args:
            text: Product title or description
            
        Returns:
            QuantityInfo object or None if no quantity found
        """
        # Clean the text
        text = text.lower().strip()
        
        # Patterns for quantity extraction
        patterns = [
            # Standard patterns: 250ml, 1.5L, 500g, etc.
            r'(\d+(?:\.\d+)?)\s*(ml|l|liter|litre|g|gm|gram|kg|kilogram|oz|fl\s*oz|pint|quart|gallon)\b',
            # With parentheses: (250ml), [1L]
            r'[\(\[](\d+(?:\.\d+)?)\s*(ml|l|liter|litre|g|gm|gram|kg|kilogram|oz|fl\s*oz)[\)\]]',
            # With x: 2x250ml, 3x500g
            r'\d+\s*x\s*(\d+(?:\.\d+)?)\s*(ml|l|liter|litre|g|gm|gram|kg|kilogram)',
            # Pack sizes: 250ml pack, 1kg pack
            r'(\d+(?:\.\d+)?)\s*(ml|l|liter|litre|g|gm|gram|kg|kilogram)\s*pack',
            # Size specifications: size 250ml
            r'size\s+(\d+(?:\.\d+)?)\s*(ml|l|liter|litre|g|gm|gram|kg|kilogram)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Take the first meaningful match
                value_str, unit = matches[0]
                try:
                    value = float(value_str)
                    unit = unit.replace(' ', '').lower()  # Clean unit
                    
                    # Convert to normalized ml
                    normalized_ml = value * self.UNIT_CONVERSIONS.get(unit, 1)
                    
                    return QuantityInfo(
                        value=value,
                        unit=unit,
                        original_text=f"{value}{unit}",
                        normalized_ml=normalized_ml
                    )
                except ValueError:
                    continue
        
        return None
    
    def is_quantity_match(self, target_quantity: str, product_quantity: str) -> Tuple[bool, float]:
        """
        Check if product quantity matches target with tolerance
        
        Args:
            target_quantity: User's desired quantity (e.g., "250ml")
            product_quantity: Product's quantity from title
            
        Returns:
            Tuple of (is_match, similarity_score)
        """
        target_info = self.extract_quantity(target_quantity)
        product_info = self.extract_quantity(product_quantity)
        
        if not target_info or not product_info:
            return False, 0.0
        
        # Calculate the difference
        target_ml = target_info.normalized_ml
        product_ml = product_info.normalized_ml
        
        if target_ml == 0:
            return False, 0.0
        
        # Calculate percentage difference
        diff_percentage = abs(product_ml - target_ml) / target_ml
        
        # Check if within tolerance
        is_match = diff_percentage <= self.tolerance
        
        # Calculate similarity score (higher is better)
        similarity_score = max(0, 1 - diff_percentage)
        
        return is_match, similarity_score
    
    def filter_products_by_quantity(self, products: List[Dict], target_quantity: Optional[str]) -> List[Dict]:
        """
        Filter products based on quantity matching
        
        Args:
            products: List of product dictionaries
            target_quantity: Target quantity string
            
        Returns:
            Filtered and sorted list of products
        """
        if not target_quantity:
            return products
        
        matched_products = []
        similar_products = []
        
        for product in products:
            title = product.get('title', '')
            
            # Extract quantity from product title
            product_quantity_info = self.extract_quantity(title)
            
            if product_quantity_info:
                is_match, similarity = self.is_quantity_match(target_quantity, title)
                
                # Add similarity score to product
                product['quantity_similarity'] = similarity
                product['extracted_quantity'] = product_quantity_info.original_text
                
                if is_match:
                    matched_products.append(product)
                elif similarity > 0.3:  # Keep somewhat similar products
                    similar_products.append(product)
        
        # Sort by similarity score
        matched_products.sort(key=lambda x: x.get('quantity_similarity', 0), reverse=True)
        similar_products.sort(key=lambda x: x.get('quantity_similarity', 0), reverse=True)
        
        # Return matched products first, then similar ones
        result = matched_products + similar_products[:3]  # Limit similar products
        
        return result[:10]  # Return top 10 results
    
    def get_quantity_message(self, target_quantity: Optional[str], filtered_count: int, total_count: int) -> str:
        """
        Generate informative message about quantity filtering
        
        Args:
            target_quantity: Target quantity string
            filtered_count: Number of products after filtering
            total_count: Total products before filtering
            
        Returns:
            Informative message string
        """
        if not target_quantity:
            return f"Showing all {total_count} products"
        
        if filtered_count == 0:
            return f"No products found for {target_quantity}. Try a different quantity."
        
        if filtered_count < total_count:
            return f"Showing {filtered_count} products matching {target_quantity} (±20% range)"
        
        return f"Showing {filtered_count} products for {target_quantity}"
    
    def suggest_alternative_quantities(self, target_quantity: str, available_quantities: List[str]) -> List[str]:
        """
        Suggest alternative quantities when exact match not found
        
        Args:
            target_quantity: User's target quantity
            available_quantities: List of available quantities
            
        Returns:
            List of suggested quantities
        """
        target_info = self.extract_quantity(target_quantity)
        if not target_info:
            return []
        
        suggestions = []
        target_ml = target_info.normalized_ml
        
        for qty in available_quantities:
            qty_info = self.extract_quantity(qty)
            if qty_info:
                diff = abs(qty_info.normalized_ml - target_ml) / target_ml
                if 0.2 < diff <= 0.5:  # 20-50% difference
                    suggestions.append(qty_info.original_text)
        
        return sorted(suggestions, key=lambda x: self.extract_quantity(x).normalized_ml)[:3]

# Utility functions for UI
def format_quantity_range(target_quantity: str, tolerance: float = 0.2) -> str:
    """Format quantity range for display"""
    matcher = QuantityMatcher(tolerance * 100)
    target_info = matcher.extract_quantity(target_quantity)
    
    if not target_info:
        return target_quantity
    
    min_val = target_info.value * (1 - tolerance)
    max_val = target_info.value * (1 + tolerance)
    
    return f"{min_val:.0f}-{max_val:.0f}{target_info.unit}"

def get_product_category(product_name: str) -> str:
    """Determine product category from name"""
    name_lower = product_name.lower()
    
    if any(word in name_lower for word in ['detergent', 'washing', 'laundry']):
        return 'detergent'
    elif any(word in name_lower for word in ['soap', 'bar']):
        return 'soap'
    elif any(word in name_lower for word in ['shampoo', 'hair']):
        return 'shampoo'
    elif any(word in name_lower for word in ['oil']):
        return 'oil'
    elif any(word in name_lower for word in ['powder']):
        return 'powder'
    elif any(word in name_lower for word in ['liquid']):
        return 'liquid'
    
    return 'general'