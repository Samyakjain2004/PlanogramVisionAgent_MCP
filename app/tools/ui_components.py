"""
Professional UI Components for E-commerce Price Comparison
Provides clean, modern UI elements similar to Amazon/Flipkart
"""

import streamlit as st
from typing import Dict, List, Optional

class PlatformBadge:
    """Generate platform badges with proper branding"""
    
    PLATFORM_COLORS = {
        'amazon': {'bg': '#FF9900', 'text': 'white', 'name': 'Amazon India'},
        'flipkart': {'bg': '#2874F0', 'text': 'white', 'name': 'Flipkart'},
        'jiomart': {'bg': '#008ECC', 'text': 'white', 'name': 'JioMart'},
        'myntra': {'bg': '#FF3E6C', 'text': 'white', 'name': 'Myntra'},
        'snapdeal': {'bg': '#E53E3E', 'text': 'white', 'name': 'Snapdeal'},
        'paytm': {'bg': '#00BAF2', 'text': 'white', 'name': 'Paytm Mall'},
        'bigbasket': {'bg': '#84C341', 'text': 'white', 'name': 'BigBasket'},
        'nykaa': {'bg': '#FC2779', 'text': 'white', 'name': 'Nykaa'},
        'tatacliq': {'bg': '#019CDB', 'text': 'white', 'name': 'Tata CLiQ'},
        'zepto': {'bg': '#6C5CE7', 'text': 'white', 'name': 'Zepto'},
        'blinkit': {'bg': '#FCDC00', 'text': 'black', 'name': 'Blinkit'},
        'croma': {'bg': '#7B68EE', 'text': 'white', 'name': 'Croma'},
        'lenskart': {'bg': '#0DB7C4', 'text': 'white', 'name': 'Lenskart'},
        'pharmeasy': {'bg': '#06C270', 'text': 'white', 'name': 'PharmEasy'},
        'netmeds': {'bg': '#00A99D', 'text': 'white', 'name': 'Netmeds'},
        'firstcry': {'bg': '#FFA500', 'text': 'white', 'name': 'FirstCry'},
        'purplle': {'bg': '#7C4DFF', 'text': 'white', 'name': 'Purplle'},
        'reliance': {'bg': '#1976D2', 'text': 'white', 'name': 'Reliance Digital'},
        'shopclues': {'bg': '#FF6B35', 'text': 'white', 'name': 'ShopClues'},
        'vijaysales': {'bg': '#FF6B00', 'text': 'white', 'name': 'Vijay Sales'},
        'default': {'bg': '#6C757D', 'text': 'white', 'name': 'Online Store'}
    }
    
    @staticmethod
    def detect_platform(url: str, title: str = "") -> str:
        """Detect platform from URL or title"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if 'amazon' in url_lower or 'amazon' in title_lower:
            return 'amazon'
        elif 'flipkart' in url_lower or 'flipkart' in title_lower:
            return 'flipkart'
        elif 'jio' in url_lower or 'jiomart' in title_lower:
            return 'jiomart'
        elif 'myntra' in url_lower or 'myntra' in title_lower:
            return 'myntra'
        elif 'snapdeal' in url_lower or 'snapdeal' in title_lower:
            return 'snapdeal'
        elif 'paytm' in url_lower or 'paytm' in title_lower:
            return 'paytm'
        elif 'bigbasket' in url_lower or 'bigbasket' in title_lower:
            return 'bigbasket'
        elif 'nykaa' in url_lower or 'nykaa' in title_lower:
            return 'nykaa'
        elif 'tatacliq' in url_lower or 'tatacliq' in title_lower:
            return 'tatacliq'
        elif 'zepto' in url_lower or 'zepto' in title_lower:
            return 'zepto'
        elif 'blinkit' in url_lower or 'grofers' in url_lower or 'blinkit' in title_lower:
            return 'blinkit'
        elif 'croma' in url_lower or 'croma' in title_lower:
            return 'croma'
        elif 'lenskart' in url_lower or 'lenskart' in title_lower:
            return 'lenskart'
        elif 'pharmeasy' in url_lower or 'pharmeasy' in title_lower:
            return 'pharmeasy'
        elif 'netmeds' in url_lower or 'netmeds' in title_lower:
            return 'netmeds'
        elif 'firstcry' in url_lower or 'firstcry' in title_lower:
            return 'firstcry'
        elif 'purplle' in url_lower or 'purplle' in title_lower:
            return 'purplle'
        elif 'reliance' in url_lower or 'reliance' in title_lower:
            return 'reliance'
        elif 'shopclues' in url_lower or 'shopclues' in title_lower:
            return 'shopclues'
        elif 'vijaysales' in url_lower or 'vijaysales' in title_lower:
            return 'vijaysales'
        else:
            return 'default'
    
    @staticmethod
    def generate_badge(platform: str) -> str:
        """Generate HTML badge for platform"""
        config = PlatformBadge.PLATFORM_COLORS.get(platform, PlatformBadge.PLATFORM_COLORS['default'])
        
        return f'<div style="background: {config["bg"]}; color: {config["text"]}; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 8px;">{config["name"]}</div>'

class ProductCard:
    """Professional product card component"""
    
    @staticmethod
    def create_card(product_data: Dict, rank: int, show_comparison: bool = True) -> str:
        """
        Create a professional product card
        
        Args:
            product_data: Product information dictionary
            rank: Product ranking (1, 2, 3...)
            show_comparison: Whether to show comparison info
        """
        # Extract data with defaults
        title = product_data.get('title', 'Product Title')[:60] + "..." if len(product_data.get('title', '')) > 60 else product_data.get('title', 'Product Title')
        price = product_data.get('price', '₹N/A')
        rating = product_data.get('rating', '4.0')
        review_count = product_data.get('review_count', '0')
        image_url = product_data.get('image', 'https://via.placeholder.com/150x150.png?text=No+Image')
        product_url = product_data.get('link', '#')
        platform = product_data.get('platform', 'default')
        delivery_info = product_data.get('delivery', '')
        savings = product_data.get('savings', '')
        quantity_info = product_data.get('extracted_quantity', '')
        
        # Generate platform badge
        platform_badge = PlatformBadge.generate_badge(platform)
        
        # Create savings display
        savings_html = ""
        if savings and savings != "₹0":
            savings_html = f'<div style="background: #E8F5E8; color: #27AE60; padding: 3px 8px; border-radius: 8px; font-size: 11px; font-weight: bold; margin-bottom: 5px; display: inline-block;">Save {savings}</div>'
        
        # Create quantity display
        quantity_html = ""
        if quantity_info:
            quantity_html = f'<div style="background: #F0F8FF; color: #2E86C1; padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: bold; margin-bottom: 5px; display: inline-block;">{quantity_info}</div>'
        
        # Create delivery info
        delivery_html = ""
        if delivery_info:
            delivery_html = f'<div style="font-size: 12px; color: #27AE60; margin: 5px 0;"><span style="margin-right: 5px;">🚚</span>{delivery_info}</div>'
        
        # Create the card - completely clean HTML with no formatting
        card_html = f'<div style="border: 1px solid #E5E5E5; border-radius: 12px; padding: 16px; margin-bottom: 20px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.08); position: relative;"><div style="position: absolute; top: -8px; left: 12px; background: #FF6B6B; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold;">{rank}</div><div style="text-align: right; margin-bottom: 10px;">{platform_badge}</div><div style="text-align: center; margin-bottom: 15px;"><img src="{image_url}" style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; border: 1px solid #E5E5E5;" alt="Product Image" onerror="this.src=\'https://via.placeholder.com/120x120.png?text=No+Image\'"></div><h4 style="margin: 0 0 10px 0; font-size: 14px; color: #333; line-height: 1.4; font-weight: 600; text-align: center;">{title}</h4><div style="text-align: center; margin-bottom: 8px;">{quantity_html}</div><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><div style="font-size: 20px; font-weight: bold; color: #B12704;">{price}</div><div style="display: flex; align-items: center;"><span style="color: #FF9500; margin-right: 4px; font-size: 14px;">★</span><span style="font-size: 13px; color: #565959;">{rating} ({review_count})</span></div></div><div style="text-align: center; margin-bottom: 8px;">{savings_html}</div>{delivery_html}<div style="text-align: center; margin-top: 15px;"><a href="{product_url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #FF6B6B 0%, #FF5252 100%); color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 14px; box-shadow: 0 3px 10px rgba(255, 107, 107, 0.3);">🛒 Buy Now</a></div></div>'
        
        return f'<div>{card_html}</div>'


class ComparisonTable:
    """Professional comparison table component"""
    
    @staticmethod
    def create_comparison_header(product_name: str, quantity: str = "", total_results: int = 0) -> str:
        """Create comparison header with search info"""
        quantity_text = f" ({quantity})" if quantity else ""
        
        return f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h2 style="margin: 0; font-size: 24px; font-weight: 600;">
                🛒 Smart Price Comparison
            </h2>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                {product_name}{quantity_text} • {total_results} products found
            </p>
        </div>
        """
    
    @staticmethod
    def create_best_deal_banner(product_data: Dict) -> str:
        """Create best deal banner"""
        title = product_data.get('title', 'Product')[:40] + "..." if len(product_data.get('title', '')) > 40 else product_data.get('title', 'Product')
        price = product_data.get('price', '₹N/A')
        platform = product_data.get('platform', 'default')
        platform_name = PlatformBadge.PLATFORM_COLORS.get(platform, PlatformBadge.PLATFORM_COLORS['default'])['name']

        return f"""
        <div style="
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            border-left: 5px solid #FFD700;
        ">
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                🏆 Best Deal Found!
            </div>
            <div style="font-size: 14px;">
                <strong>{title}</strong> at <strong>{price}</strong> on {platform_name}
            </div>
        </div>
        """
@staticmethod
def create_card(product_data: Dict, rank: int, show_comparison: bool = True, is_best_deal: bool = False) -> str:
    """Create a professional product card"""

    # Extract data with fallbacks
    raw_title = product_data.get('title', '')
    title = (raw_title[:60] + "...") if raw_title and len(raw_title) > 60 else raw_title
    price = product_data.get('price', '')
    rating = product_data.get('rating', '')
    review_count = product_data.get('review_count', '')
    image_url = product_data.get('image', 'https://via.placeholder.com/150x150.png?text=No+Image')
    product_url = product_data.get('link', '')
    platform = product_data.get('platform', 'default')
    delivery_info = product_data.get('delivery', '')
    savings = product_data.get('savings', '')
    quantity_info = product_data.get('extracted_quantity', '')

    # Badges and optional tags
    platform_badge = PlatformBadge.generate_badge(platform)

    savings_html = f'<div style="background: #E8F5E8; color: #27AE60; padding: 3px 8px; border-radius: 8px; font-size: 11px; font-weight: bold; margin-bottom: 5px; display: inline-block;">Save {savings}</div>' if savings and savings != "₹0" else '&nbsp;'

    quantity_html = f'<div style="background: #F0F8FF; color: #2E86C1; padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: bold; margin-bottom: 5px; display: inline-block;">{quantity_info}</div>' if quantity_info else '&nbsp;'

    delivery_html = f'<div style="font-size: 12px; color: #27AE60; margin: 5px 0;"><span style="margin-right: 5px;">🚚</span>{delivery_info}</div>' if delivery_info else '&nbsp;'

    title_html = f'<h4 style="margin: 0 0 10px 0; font-size: 14px; color: #333; line-height: 1.4; font-weight: 600; text-align: center;">{title}</h4>' if title else '<div style="height: 32px;">&nbsp;</div>'

    price_html = f'<div style="font-size: 20px; font-weight: bold; color: #B12704;">{price}</div>' if price else '<div style="height: 24px;">&nbsp;</div>'

    rating_html = f'<div style="display: flex; align-items: center;"><span style="color: #FF9500; margin-right: 4px; font-size: 14px;">★</span><span style="font-size: 13px; color: #565959;">{rating} ({review_count})</span></div>' if rating else '&nbsp;'

    button_html = f'<a href="{product_url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #FF6B6B 0%, #FF5252 100%); color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 14px; box-shadow: 0 3px 10px rgba(255, 107, 107, 0.3);">🛒 Buy Now</a>' if product_url and product_url != '#' else '&nbsp;'

    # Add best deal ribbon
    best_deal_ribbon = ''
    if is_best_deal:
        best_deal_ribbon = '''
            <div style="
                position: absolute;
                top: 0;
                right: 0;
                background: #28a745;
                color: white;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
                border-top-right-radius: 12px;
                border-bottom-left-radius: 12px;
                z-index: 10;
            ">
                🏆 Best Deal
            </div>
        '''

    card_html = f'''
    <div style="border: 1px solid #E5E5E5; border-radius: 12px; padding: 16px; margin-bottom: 20px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.08); position: relative; height: 420px;">
        <div style="position: absolute; top: -8px; left: 12px; background: #FF6B6B; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold;">{rank}</div>
        <div style="text-align: right; margin-bottom: 10px;">{platform_badge}</div>
        <div style="text-align: center; margin-bottom: 15px;">
            <img src="{image_url}" style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; border: 1px solid #E5E5E5;" alt="Product Image" onerror="this.src='https://via.placeholder.com/120x120.png?text=No+Image'">
        </div>
        {title_html}
        <div style="text-align: center; margin-bottom: 8px;">{quantity_html}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            {price_html}
            {rating_html}
        </div>
        <div style="text-align: center; margin-bottom: 8px;">{savings_html}</div>
        {delivery_html}
        <div style="text-align: center; margin-top: 15px;">{button_html}</div>
    </div>
    '''

    return f'<div>{card_html}</div>'

class FilteringInfo:
    """Display filtering and sorting information"""
    
    @staticmethod
    def create_filter_summary(
        total_found: int, 
        filtered_count: int, 
        target_quantity: str = "", 
        sort_by: str = "",
        filter_message: str = ""
    ) -> str:
        """Create filtering summary information"""
        
        # Determine filter status
        if target_quantity and filtered_count < total_found:
            filter_status = f"Filtered to {filtered_count} products matching {target_quantity} (±20% range)"
        elif target_quantity:
            filter_status = f"All {filtered_count} products match {target_quantity}"
        else:
            filter_status = f"Showing all {total_found} products"
        
        # Sort information
        sort_info = ""
        if sort_by:
            sort_mapping = {
                "price_low": "💰 Price: Low to High",
                "price_high": "💰 Price: High to Low", 
                "rating": "⭐ Rating: High to Low",
                "popularity": "🔥 Most Popular",
                "newest": "🆕 Newest First"
            }
            sort_info = f" • Sorted by {sort_mapping.get(sort_by, sort_by)}"
        
        return f"""
        <div style="
            background: #F8F9FA;
            border: 1px solid #E9ECEF;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 15px;
            font-size: 13px;
            color: #495057;
        ">
            📊 {filter_status}{sort_info}
            {f" • {filter_message}" if filter_message else ""}
        </div>
        """

class LoadingComponents:
    """Loading and progress components"""
    
    @staticmethod
    def show_search_progress(step: str):
        """Show search progress"""
        steps = {
            "api": "🔍 Searching products...",
            "filter": "🎯 Filtering by quantity...",
            "sort": "📊 Sorting results...",
            "ai": "🤖 Getting AI recommendations...",
            "display": "✨ Preparing display..."
        }
        
        message = steps.get(step, step)
        
        # Create progress bar with Streamlit
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text(message)
        
        return progress_bar, status_text