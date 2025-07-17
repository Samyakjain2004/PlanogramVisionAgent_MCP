import os
import requests
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union
from recommendation_engine import RecommendationEngine, SortCriteria, QuantityMatcher
from product_analyzer import ProductAnalyzer

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")  # Or load from .env using dotenv

def compare_prices(product_name: str, quantity: Optional[str] = None, 
                  sort_by: str = "recommendation", limit: int = 5) -> dict:
    print(f"[🛡 SERPAPI KEY]: {SERPAPI_KEY}")
    print(f"[🔎 SerpAPI] Searching for: {product_name}")

    url = "https://serpapi.com/search.json"  # Use `.json` for cleaner output
    # Construct enhanced search query
    enhanced_query = f"{product_name} buy online india"
    if quantity:
        enhanced_query = f"{product_name} {quantity} buy online india"
    
    params = {
        "engine": "google_shopping",
        "q": enhanced_query,
        "api_key": SERPAPI_KEY,
        "hl": "en",          # English language
        "gl": "in",          # Location set to India
        "location": "India", # Explicit location
        "currency": "₹",     # Currency in Rupees
        "country": "in",     # Country code for India
        "google_domain": "google.co.in",  # Use Indian Google domain
        "num": "20",         # Get more results for better filtering
        "sort": "r",         # Sort by relevance initially
        "prmd": "sinv",      # Include shopping, images, news, videos
        "tbm": "shop"        # Shopping results
    }

    try:
        # Adding timeout parameters to avoid hanging
        response = requests.get(url, params=params, timeout=15)  # Increased timeout to 15 seconds
        
        # Check if the response is valid
        if response.status_code != 200:
            print(f"[⚠️ SerpAPI Request] Error status code: {response.status_code}")
            return {"Error": f"API returned error status: {response.status_code}"}
        
        data = response.json()
        print(f"[📦 SerpAPI Response Status]: Received data for {product_name}")
        
        # Check if we have valid shopping results
        shopping_results = data.get("shopping_results", [])
        if not shopping_results:
            print("[⚠️ SerpAPI Request] No shopping results found")
            return {"Error": f"No product information found for '{product_name}'"}

        # Initialize recommendation engine and product analyzer
        recommendation_engine = RecommendationEngine()
        product_analyzer = ProductAnalyzer()
        
        # Process and clean raw results
        processed_products = []
        for item in shopping_results:
            title = item.get("title", "Unknown")
            price = item.get("price", "N/A")
            link = item.get("product_link", "#")
            source = item.get("source", "Unknown Seller")
            thumbnail = item.get("thumbnail", "")
            
            # Skip invalid products
            if not title or title == "Unknown" or price == "N/A":
                continue
                
            # Clean up source name
            source = source.replace(".com", "").replace(".co.in", "").title()
            
            # Ensure thumbnail URL is valid
            if not thumbnail or not thumbnail.startswith("http"):
                thumbnail = "https://via.placeholder.com/100x100.png?text=No+Image"
            
            processed_products.append({
                "title": title,
                "price": price,
                "product_link": link,
                "source": source,
                "thumbnail": thumbnail
            })
        
        # Apply quantity filtering if specified
        if quantity:
            try:
                # Parse quantity (e.g., "500ml", "1kg", "2 pieces")
                import re
                qty_match = re.search(r'(\d+(?:\.\d+)?)\s*(\w+)', quantity)
                if qty_match:
                    qty_value, qty_unit = qty_match.groups()
                    filtered_products = QuantityMatcher.filter_by_quantity(
                        processed_products, float(qty_value), qty_unit
                    )
                    if filtered_products:
                        processed_products = filtered_products
                        print(f"[✅ Quantity Filter] Found {len(filtered_products)} products matching {quantity}")
                    else:
                        print(f"[⚠️ Quantity Filter] No products found matching {quantity}, showing all results")
            except Exception as e:
                print(f"[⚠️ Quantity Filter] Error filtering by quantity: {e}")
        
        # Convert sort_by string to enum
        sort_criteria_map = {
            "recommendation": SortCriteria.RECOMMENDATION_SCORE,
            "price_low": SortCriteria.PRICE_LOW_TO_HIGH,
            "price_high": SortCriteria.PRICE_HIGH_TO_LOW,
            "rating": SortCriteria.RATING_HIGH_TO_LOW,
            "reviews": SortCriteria.REVIEWS_HIGH_TO_LOW,
            "delivery": SortCriteria.DELIVERY_FASTEST
        }
        
        sort_criteria = sort_criteria_map.get(sort_by, SortCriteria.RECOMMENDATION_SCORE)
        
        # Rank products using recommendation engine
        ranked_products = recommendation_engine.rank_products(
            processed_products, sort_criteria, limit
        )
        
        if not ranked_products:
            return {"Error": "No suitable products found after analysis"}
        
        # Generate results with recommendation explanations
        results = {}
        for i, product in enumerate(ranked_products):
            # Generate smart explanation
            explanation = product_analyzer.generate_smart_explanation(
                {
                    "title": product.title,
                    "price": f"₹{product.price}",
                    "source": product.source
                },
                i + 1,
                len(ranked_products)
            )
            
            # Format price
            price_display = f"₹{product.price}" if "₹" not in str(product.price) else str(product.price)
            
            # Create enhanced product display
            key = f"#{i+1} {product.source} - {product.title[:25]}..."
            value = (
                f'<img src="{product.image_url}" width="100" onerror="this.onerror=null; this.src=\'https://via.placeholder.com/100x100.png?text=Error\'"><br>'
                f"**{product.title[:60]}**  \n"
                f"💰 **Price**: {price_display}  \n"
                f"⭐ **Rating**: {product.rating:.1f}/5 ({product.review_count} reviews)  \n"
                f"🚚 **Delivery**: {product.delivery_days} days  \n"
                f"🎯 **Why**: {explanation}  \n"
                f"📊 **Score**: {product.overall_score:.2f}  \n"
                f"🔗 [Buy Now]({product.product_url})"
            )
            results[key] = value
        
        # Add comparison summary
        if len(ranked_products) > 1:
            comparison = product_analyzer.compare_products(
                [{"title": p.title, "price": p.price, "source": p.source} for p in ranked_products[:3]]
            )
            
            results["🏆 AI Recommendation Summary"] = (
                f"**Best Choice**: {comparison.winner}  \n"
                f"**Why**: {comparison.comparison_summary}  \n"
                f"**Confidence**: {comparison.confidence_score:.0%}"
            )

        return results or {"Error": "No results found for this product."}

    except requests.exceptions.Timeout:
        print("[⚠️ SerpAPI Request] Timeout error while fetching prices")
        return {"Error": "Request timed out. Please try again later."}
    except requests.exceptions.ConnectionError:
        print("[⚠️ SerpAPI Request] Connection error while fetching prices")
        return {"Error": "Network connection error. Please check your internet connection."}
    except requests.exceptions.RequestException as e:
        print(f"[⚠️ SerpAPI Request] Request error: {str(e)}")
        return {"Error": f"Request error: {str(e)}"}
    except Exception as e:
        print(f"[⚠️ SerpAPI Request] General error: {str(e)}")
        return {"Error": f"Failed to fetch prices: {str(e)}"}

def advanced_product_search(product_name: str, quantity: Optional[str] = None, 
                          sort_by: str = "recommendation", price_range: Optional[tuple] = None,
                          min_rating: float = 0.0, limit: int = 5) -> dict:
    """
    Advanced product search with comprehensive filtering and recommendation
    
    Args:
        product_name: Product to search for
        quantity: Specific quantity (e.g., "500ml", "1kg")
        sort_by: Sorting criteria (recommendation, price_low, price_high, rating, reviews, delivery)
        price_range: Tuple of (min_price, max_price) in rupees
        min_rating: Minimum rating threshold
        limit: Maximum number of results
    
    Returns:
        Dictionary with ranked product recommendations
    """
    try:
        # Use the enhanced compare_prices function
        results = compare_prices(product_name, quantity, sort_by, limit)
        
        # If additional filtering is needed, apply it here
        if price_range or min_rating > 0:
            filtered_results = {}
            for key, value in results.items():
                if key.startswith("Error") or key.startswith("🏆"):
                    filtered_results[key] = value
                    continue
                
                # Extract price and rating for filtering
                import re
                price_match = re.search(r'₹([\d,]+(?:\.\d+)?)', value)
                rating_match = re.search(r'Rating\*\*: ([\d.]+)', value)
                
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                    
                    # Apply price range filter
                    if price_range:
                        min_price, max_price = price_range
                        if not (min_price <= price <= max_price):
                            continue
                
                if rating_match:
                    rating = float(rating_match.group(1))
                    
                    # Apply rating filter
                    if rating < min_rating:
                        continue
                
                filtered_results[key] = value
            
            return filtered_results
        
        return results
        
    except Exception as e:
        return {"Error": f"Advanced search failed: {str(e)}"}

def get_quantity_suggestions(product_name: str) -> List[str]:
    """
    Get smart quantity suggestions based on product type
    
    Args:
        product_name: Product name
        
    Returns:
        List of suggested quantities
    """
    product_lower = product_name.lower()
    
    # Define quantity suggestions based on product categories
    if any(word in product_lower for word in ['detergent', 'soap', 'shampoo', 'oil', 'sauce']):
        return ['250ml', '500ml', '1L', '2L', '5L']
    elif any(word in product_lower for word in ['rice', 'wheat', 'flour', 'sugar', 'salt']):
        return ['500g', '1kg', '5kg', '10kg', '25kg']
    elif any(word in product_lower for word in ['phone', 'mobile', 'laptop', 'tablet']):
        return ['1 piece', '2 pieces', 'with accessories', 'bundle pack']
    elif any(word in product_lower for word in ['medicine', 'tablet', 'capsule']):
        return ['10 tablets', '20 tablets', '30 tablets', '1 strip', '1 bottle']
    elif any(word in product_lower for word in ['biscuit', 'cookies', 'snacks']):
        return ['100g', '200g', '500g', '1kg', 'family pack']
    else:
        return ['1 piece', '2 pieces', '5 pieces', '10 pieces', 'bulk pack']
