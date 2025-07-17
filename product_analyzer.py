"""
Product Analyzer for review sentiment analysis and recommendation reasoning
Uses Azure OpenAI for intelligent product comparison and recommendation explanations
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ProductAnalysis:
    """Structured product analysis results"""
    overall_sentiment: str  # positive, negative, neutral
    sentiment_score: float  # 0.0 to 1.0
    key_pros: List[str]
    key_cons: List[str]
    recommendation_reason: str
    quality_score: float  # 0.0 to 1.0
    value_score: float  # 0.0 to 1.0
    trust_score: float  # 0.0 to 1.0

@dataclass
class ComparisonResult:
    """Product comparison results"""
    winner: str
    comparison_summary: str
    detailed_reasoning: str
    recommendation: str
    confidence_score: float

class ProductAnalyzer:
    """Advanced product analyzer using Azure OpenAI"""
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    def analyze_product_reviews(self, product_title: str, price: float, 
                              mock_reviews: List[str] = None) -> ProductAnalysis:
        """Analyze product reviews and generate insights"""
        
        # For now, use mock reviews. In production, these would come from web scraping
        reviews = mock_reviews or self._generate_mock_reviews(product_title)
        
        prompt = f"""
        Analyze the following product and its reviews to provide comprehensive insights:
        
        Product: {product_title}
        Price: ₹{price}
        
        Reviews:
        {chr(10).join(f"- {review}" for review in reviews)}
        
        Please provide a detailed analysis in the following JSON format:
        {{
            "overall_sentiment": "positive/negative/neutral",
            "sentiment_score": 0.0-1.0,
            "key_pros": ["pro1", "pro2", "pro3"],
            "key_cons": ["con1", "con2", "con3"],
            "recommendation_reason": "brief explanation why to buy/avoid",
            "quality_score": 0.0-1.0,
            "value_score": 0.0-1.0,
            "trust_score": 0.0-1.0
        }}
        
        Focus on:
        1. Overall sentiment from reviews
        2. Key advantages and disadvantages
        3. Value for money assessment
        4. Quality and reliability indicators
        5. Trustworthiness of the product
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert product analyst specializing in e-commerce product evaluation. Provide accurate, helpful analysis based on customer reviews and product information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse JSON response
            analysis_text = response.choices[0].message.content
            analysis_data = self._extract_json_from_response(analysis_text)
            
            return ProductAnalysis(
                overall_sentiment=analysis_data.get('overall_sentiment', 'neutral'),
                sentiment_score=float(analysis_data.get('sentiment_score', 0.5)),
                key_pros=analysis_data.get('key_pros', []),
                key_cons=analysis_data.get('key_cons', []),
                recommendation_reason=analysis_data.get('recommendation_reason', ''),
                quality_score=float(analysis_data.get('quality_score', 0.5)),
                value_score=float(analysis_data.get('value_score', 0.5)),
                trust_score=float(analysis_data.get('trust_score', 0.5))
            )
            
        except Exception as e:
            print(f"Error analyzing product: {e}")
            return ProductAnalysis(
                overall_sentiment='neutral',
                sentiment_score=0.5,
                key_pros=['Available for purchase'],
                key_cons=['Analysis unavailable'],
                recommendation_reason='Analysis could not be completed',
                quality_score=0.5,
                value_score=0.5,
                trust_score=0.5
            )
    
    def compare_products(self, products: List[Dict], 
                        user_priorities: Dict[str, float] = None) -> ComparisonResult:
        """Compare multiple products and provide recommendation"""
        
        if len(products) < 2:
            return ComparisonResult(
                winner="insufficient_data",
                comparison_summary="Need at least 2 products to compare",
                detailed_reasoning="More products needed for comparison",
                recommendation="Add more products to compare",
                confidence_score=0.0
            )
        
        # Default priorities
        priorities = user_priorities or {
            'price': 0.3,
            'quality': 0.25,
            'reviews': 0.25,
            'delivery': 0.2
        }
        
        # Prepare product comparison data
        product_data = []
        for i, product in enumerate(products[:5]):  # Limit to top 5
            product_data.append({
                'id': i + 1,
                'title': product.get('title', 'Unknown')[:50],
                'price': product.get('price', '₹0'),
                'source': product.get('source', 'Unknown'),
                'rating': getattr(product, 'rating', 4.0),
                'review_count': getattr(product, 'review_count', 100)
            })
        
        prompt = f"""
        Compare these products and provide a comprehensive recommendation:
        
        Products to compare:
        {json.dumps(product_data, indent=2)}
        
        User priorities:
        {json.dumps(priorities, indent=2)}
        
        Provide your analysis in the following JSON format:
        {{
            "winner": "Product title or ID",
            "comparison_summary": "Brief 2-3 sentence summary",
            "detailed_reasoning": "Detailed explanation of why this product is best",
            "recommendation": "Final recommendation with actionable advice",
            "confidence_score": 0.0-1.0
        }}
        
        Consider:
        1. Price-to-value ratio
        2. Product quality and reliability
        3. Customer satisfaction (reviews/ratings)
        4. Delivery and availability
        5. Overall best choice for the user
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert product comparison specialist. Provide detailed, objective analysis to help users make informed purchasing decisions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            # Parse JSON response
            comparison_text = response.choices[0].message.content
            comparison_data = self._extract_json_from_response(comparison_text)
            
            return ComparisonResult(
                winner=comparison_data.get('winner', 'Unable to determine'),
                comparison_summary=comparison_data.get('comparison_summary', 'Analysis unavailable'),
                detailed_reasoning=comparison_data.get('detailed_reasoning', 'Detailed analysis unavailable'),
                recommendation=comparison_data.get('recommendation', 'Please review options carefully'),
                confidence_score=float(comparison_data.get('confidence_score', 0.5))
            )
            
        except Exception as e:
            print(f"Error comparing products: {e}")
            return ComparisonResult(
                winner="analysis_error",
                comparison_summary="Unable to complete comparison analysis",
                detailed_reasoning="Technical error occurred during analysis",
                recommendation="Please try again or compare manually",
                confidence_score=0.0
            )
    
    def generate_smart_explanation(self, product: Dict, rank: int, 
                                 total_products: int) -> str:
        """Generate smart explanation for why a product is recommended"""
        
        prompt = f"""
        Generate a brief, compelling explanation for why this product is ranked #{rank} out of {total_products}:
        
        Product: {product.get('title', 'Unknown')}
        Price: {product.get('price', '₹0')}
        Source: {product.get('source', 'Unknown')}
        Rank: #{rank}
        
        Provide a single, impactful sentence (max 15 words) explaining why this product is recommended.
        Focus on the key selling point that makes it stand out.
        
        Examples:
        - "Best value for money with excellent customer reviews"
        - "Premium quality with fast delivery from trusted seller"
        - "Lowest price available with good ratings"
        - "Top-rated product with proven reliability"
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise product recommendation expert. Create brief, impactful explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=50
            )
            
            explanation = response.choices[0].message.content.strip()
            # Remove quotes if present
            explanation = explanation.strip('"\'')
            
            return explanation
            
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return f"#{rank} recommended choice"
    
    def _extract_json_from_response(self, text: str) -> Dict:
        """Extract JSON from AI response"""
        try:
            # Try to find JSON in the response
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            else:
                # If no JSON found, return empty dict
                return {}
                
        except json.JSONDecodeError:
            print(f"Failed to parse JSON from response: {text}")
            return {}
    
    def _generate_mock_reviews(self, product_title: str) -> List[str]:
        """Generate mock reviews for testing (will be replaced with real scraping)"""
        product_lower = product_title.lower()
        
        # Generate context-appropriate mock reviews
        if 'detergent' in product_lower or 'tide' in product_lower:
            return [
                "Great cleaning power, removes tough stains easily",
                "Good value for money, lasts long",
                "Pleasant fragrance, clothes smell fresh",
                "Works well in both top and front load machines",
                "Packaging could be better, but product is excellent"
            ]
        elif 'phone' in product_lower or 'mobile' in product_lower:
            return [
                "Excellent battery life, lasts full day",
                "Camera quality is impressive for this price",
                "Fast performance, no lag during usage",
                "Build quality feels premium",
                "Good display but could be brighter"
            ]
        elif 'laptop' in product_lower or 'computer' in product_lower:
            return [
                "Fast boot time and smooth performance",
                "Good build quality, feels sturdy",
                "Keyboard is comfortable for long typing",
                "Battery life is decent for work use",
                "Display is clear but not the brightest"
            ]
        else:
            return [
                "Good quality product, satisfied with purchase",
                "Delivery was quick and packaging was secure",
                "Value for money is reasonable",
                "Product matches description",
                "Would recommend to others"
            ]