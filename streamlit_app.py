import streamlit as st
from app.analyze import analyze_video_for_query
import tempfile
import os
import base64
import cv2
import time
from PIL import Image
from app.mcp_server import invoke_tool
from app.tools.price_compare import compare_prices, advanced_product_search, get_quantity_suggestions
import asyncio
from app.analyze import analyze_video_for_query_async  # Update path if needed

st.markdown("""
<style>
.product-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 24px;
    margin-top: 20px;
}
.product-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #eaeaea;
    padding: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)


def format_timestamp(ms):
    total_seconds = ms / 1000
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    subseconds = int((total_seconds - int(total_seconds)) * 100)
    return f"{minutes:02}:{seconds:02}.{subseconds:02}"

def extract_frame_at_timestamp(video_path, timestamp_ms):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_POS_MSEC, int(timestamp_ms))
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    except Exception as e:
        st.error(f"🚨 Exception while extracting frame: {str(e)}")
        return None

# === Streamlit UI ===
st.set_page_config(page_title="Planogram Vision Agent", layout="wide")

# Custom Header
st.markdown("""
    <div style='text-align: center; margin-top: -70px;'>
        <h2 style='font-size: 40px; font-family: Courier New, monospace;'>
            <img src="https://acis.affineanalytics.co.in/assets/images/logo_small.png" width="70" height="60">
            <span style='background: linear-gradient(45deg, #ed4965, #c05aaf); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                Planogram Vision Agent
            </span>
        </h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
# === Session State ===
for key in ["file_path", "file_type", "timestamps", "summary", "file_base64"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["file_path", "file_type"] else ""

import streamlit as st
import os
import base64

# === Setup ===
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.markdown("## 📤 Upload or Select Media")
#st.caption("Supported formats: MP4, MOV, AVI, MKV, JPG, JPEG, PNG")

# === Choose Mode ===
mode = st.radio("Choose Input Mode:", ["📤 Upload File", "📁 Select Existing"], horizontal=True)

# === Handle File Upload or Selection ===
uploaded_file = None
selected_prev_file = "-- None --"
file_to_use = None
file_ext = None

existing_files = sorted([
    f for f in os.listdir(UPLOAD_DIR)
    if f.lower().endswith((".mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"))
])

if mode == "📤 Upload File":
    uploaded_file = st.file_uploader("Upload an image or video")

    if uploaded_file:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        file_to_use = file_path
        file_ext = uploaded_file.name.split(".")[-1].lower()
        if uploaded_file.name not in existing_files:
            existing_files.append(uploaded_file.name)

elif mode == "📁 Select Existing":
    selected_prev_file = st.selectbox("Select from uploaded files", ["-- None --"] + existing_files)
    if selected_prev_file != "-- None --":
        file_to_use = os.path.join(UPLOAD_DIR, selected_prev_file)
        file_ext = selected_prev_file.split(".")[-1].lower()

# === Preview Selected File ===
if file_to_use:
    with st.expander("📂 Preview Selected File", expanded=False):
        try:
            with open(file_to_use, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")

            if file_ext in ["jpg", "jpeg", "png"]:
                st.image(f"data:image/{file_ext};base64,{encoded}", width=250)

            elif file_ext in ["mp4", "mov", "avi", "mkv"]:
                mime_type = f"video/{'mp4' if file_ext == 'mp4' else 'quicktime'}"
                video_html = f"""
                <video width="250" controls muted>
                    <source src="data:{mime_type};base64,{encoded}" type="{mime_type}">
                    Your browser does not support the video tag.
                </video>
                """
                st.markdown(video_html, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Couldn't load preview: {e}")


# Load and prepare file if selected/uploaded
if file_to_use:
    try:
        is_video = file_ext in ["mp4", "mov", "avi", "mkv"]
        is_image = file_ext in ["jpg", "jpeg", "png"]
        st.session_state.file_type = "video" if is_video else "image" if is_image else None

        with open(file_to_use, "rb") as f:
            file_bytes = f.read()
            st.session_state.file_base64 = base64.b64encode(file_bytes).decode("utf-8")

        st.session_state.file_path = file_to_use
    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")


# === Ask Question ===
st.markdown("### 💬 Ask Your Question")
user_query = st.text_area("Enter your question", placeholder="e.g. Where is Tide powder located?")

if st.button("🚀 Analyze"):
    if st.session_state.file_path and user_query and st.session_state.file_type:
        with st.spinner("Analyzing, please wait..."):
            try:
                result = asyncio.run(analyze_video_for_query_async(st.session_state.file_path, user_query))
                st.session_state.result = result

                # final_summary = result.get("final_summary", {})
                final_summary = result
                if isinstance(final_summary, str):
                    import json
                    try:
                        final_summary = json.loads(final_summary)
                    except json.JSONDecodeError:
                        st.warning("⚠️ Could not parse summary as JSON.")

                st.session_state.summary = final_summary
                st.session_state.timestamps = result.get("timestamps", []) if st.session_state.file_type == "video" else []
                st.success("✅ Analysis complete!")
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")

# # # === Show Summary ===
if st.session_state.summary:
    result = st.session_state.summary

    if isinstance(result, dict):
        direct_answer = result.get("direct_answer", "").strip()
        reasoning = result.get("reasoning", "").strip()

        st.markdown("### 📝 Analysis Summary")

        # Toggle to show/hide reasoning
        show_reasoning = st.toggle("🧠 Show Reasoning", value=False)

        st.markdown(f"**📌 Answer:** {direct_answer}")

        if show_reasoning and reasoning:
            st.markdown(f"**🧠 Reasoning:** {reasoning}")

# === Video Timeline and Frame View ===
# Initialize state to keep expander open after frame selection
# Initialize session state
if "show_frame_viewer" not in st.session_state:
    st.session_state["show_frame_viewer"] = False
if "selected_frame_img" not in st.session_state:
    st.session_state["selected_frame_img"] = None
if "selected_frame_caption" not in st.session_state:
    st.session_state["selected_frame_caption"] = ""

# === Video Timeline and Frame View ===
if (
    st.session_state.file_type == "video"
    and st.session_state.file_path
    and st.session_state.file_base64
    and st.session_state.summary
):
    #st.markdown("### 📊 Product Detection Timeline & Frame Viewer")

    cap = cv2.VideoCapture(st.session_state.file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration_ms = (frame_count / fps) * 1000.0 if fps > 0 else 1
    cap.release()

    markers = ""
    for ts in st.session_state.timestamps:
        left_px = (ts / duration_ms) * 576.0
        markers += f'<div class="marker" style="left:{left_px:.2f}px;" title="{format_timestamp(ts)}"></div>'

    debug_ts = 3850
    debug_left_pct = min((debug_ts / duration_ms) * 100.0, 100)
    debug_marker = f'<div class="debug-line" style="left:{debug_left_pct:.6f}%;" title="03:03.85"></div>'

    with st.expander("📊 Product Detection Timeline & Frame Viewer", expanded=st.session_state["show_frame_viewer"]):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎬 Video Timeline")
            st.markdown(
                f"""
                <div style="position:relative; width:640px; margin-bottom:8px;">
                    <video id="videoPlayer" width="640" height="360" controls muted>
                        <source src="data:video/mp4;base64,{st.session_state.file_base64}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                    <div class="timeline-overlay">
                        <div class="timeline-inner">
                            {markers}{debug_marker}
                        </div>
                    </div>
                </div>

                <style>
                .timeline-overlay {{
                    position: absolute;
                    bottom: 42px;
                    width: 640px;
                    height: 0;
                    display: flex;
                    justify-content: center;
                    pointer-events: none;
                }}
                .timeline-inner {{
                    width: 576px;
                    height: 12px;
                    position: relative;
                }}
                .marker {{
                    position: absolute;
                    width: 4px;
                    height: 6px;
                    background-color: yellow;
                    box-shadow: 0 0 4px rgba(255, 255, 0, 0.9);
                }}
                .marker:hover::after {{
                    content: attr(title);
                    position: absolute;
                    top: -28px;
                    left: -10px;
                    background: black;
                    color: white;
                    padding: 2px 5px;
                    font-size: 10px;
                    border-radius: 4px;
                    white-space: nowrap;
                }}
                .debug-line {{
                    position: absolute;
                    width: 1px;
                    height: 12px;
                    background-color: red;
                    opacity: 0.9;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

        with col2:
            if st.session_state.timestamps:
                st.markdown("#### ⏱️ Timestamp Viewer")
                formatted_map = {format_timestamp(ts): ts for ts in st.session_state.timestamps}
                formatted_list = list(formatted_map.keys())

                selected_display = st.selectbox("Select timestamp", formatted_list, key="frame_ts_select")

                if st.button("🔍 Show Frame at Timestamp"):
                    timestamp_ms = formatted_map[selected_display]
                    frame = extract_frame_at_timestamp(st.session_state.file_path, timestamp_ms)
                    if frame is not None:
                        st.session_state["selected_frame_img"] = frame
                        st.session_state["selected_frame_caption"] = f"🖼 Frame at {selected_display}"
                        st.session_state["show_frame_viewer"] = True
                    else:
                        st.warning(f"❌ No frame available at {selected_display}")
                        st.session_state["selected_frame_img"] = None

            # ✅ Show the image after rerun (if available)
            if st.session_state["show_frame_viewer"] and st.session_state["selected_frame_img"] is not None:
                st.image(
                    st.session_state["selected_frame_img"],
                    caption=st.session_state["selected_frame_caption"],
                    width=160
                )

# === Smart Price Agent Section Toggle ===
product_name = ""
if "result" in st.session_state:
    product_name = st.session_state.result.get("product_name", "")
    print(f"[🧪 Triggering SerpAPI with product: {product_name}]")
if product_name and product_name.lower() != "unknown":
    st.markdown("### 🛒 Smart Price Agent")
    show_agent = st.checkbox("Enable Smart Price Comparison and Recommendations")

    if show_agent:
        product_name = ""
        if "result" in st.session_state:
            product_name = st.session_state.result.get("product_name", "")
            print(f"[🧪 Triggering SerpAPI with product: {product_name}]")

        if product_name and product_name.lower() != "unknown":
            # Get quantity suggestions
            from app.tools.quantity_matcher import get_product_category
            category = get_product_category(product_name)

            # Quantity options based on category
            if category == 'detergent':
                quantity_suggestions = ['250ml', '500ml', '1L', '2L', '500g', '1kg']
            elif category == 'soap':
                quantity_suggestions = ['75g', '100g', '125g', '150g', '1 piece', '3 pieces']
            else:
                quantity_suggestions = ['250ml', '500ml', '1L', '500g', '1kg', '1 piece']

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown("**📦 Specify Quantity**")
                quantity_option = st.selectbox(
                    "What quantity are you looking for?",
                    ["Any quantity"] + quantity_suggestions
                )

                custom_quantity = st.text_input(
                    "Or enter custom quantity:",
                    placeholder="e.g., 750ml, 2kg, 5 pieces"
                )

            with col2:
                st.markdown("**🔄 Sort by**")
                sort_options = {
                    "🎯 Best Match": "recommendation",
                    "💰 Price: Low to High": "price_low",
                    "💰 Price: High to Low": "price_high",
                    "⭐ Rating": "rating",
                    "📝 Reviews": "reviews",
                    "🚚 Delivery": "delivery"
                }
                sort_choice = st.selectbox("Choose sorting criteria:", list(sort_options.keys()))

            with col3:
                st.markdown("**📊 Results**")
                result_count = st.slider("Number of products:", 3, 10, 5)

            st.markdown("**💸 Price Range (Optional)**")
            price_filter = st.checkbox("Filter by price range")
            min_price, max_price = 0, 50000

            if price_filter:
                price_range = st.slider("Select price range (₹):", 0, 50000, (500, 5000), step=100)
                min_price, max_price = price_range

            if st.button("🔍 Find Best Deals", type="primary"):
                final_quantity = custom_quantity or (quantity_option if quantity_option != "Any quantity" else None)
                sort_by = sort_options[sort_choice]

                with st.spinner("🤖 AI analyzing best deals across the internet..."):
                    if not os.getenv("SERPAPI_API_KEY"):
                        st.error("❌ SerpAPI key is missing. Please check your .env file.")
                    else:
                        try:
                            from app.tools.enhanced_price_scraper import enhanced_product_search
                            prices = enhanced_product_search(
                                product_name=product_name,
                                quantity=final_quantity,
                                sort_by=sort_by,
                                limit=result_count
                            )

                            if len(prices) == 1 and "Error" in prices:
                                st.error(f"❌ {prices['Error']}")
                                st.warning("Try again later or check your internet connection.")
                            else:
                                from app.tools.ui_components import ComparisonTable, ProductCard, FilteringInfo

                                header_html = ComparisonTable.create_comparison_header(
                                    product_name, final_quantity, len(prices) - 1 if '🏆' in str(prices) else len(prices)
                                )
                                st.markdown(header_html, unsafe_allow_html=True)

                                filter_info = FilteringInfo.create_filter_summary(
                                    total_found=len(prices),
                                    filtered_count=len(prices) - 1 if '🏆' in str(prices) else len(prices),
                                    target_quantity=final_quantity,
                                    sort_by=sort_choice
                                )
                                st.markdown(filter_info, unsafe_allow_html=True)

                        except Exception as e:
                            st.error(f"❌ Error fetching prices: {str(e)}")
                            st.warning("SerpAPI request failed. Please try again later.")

                        try:
                            enhanced_results = enhanced_product_search(
                                product_name=product_name,
                                quantity=final_quantity,
                                sort_by=sort_by,
                                limit=result_count
                            )
                            if "Error" in enhanced_results:
                                st.error(f"❌ {enhanced_results['Error']}")
                                enhanced_results = prices
                        except:
                            enhanced_results = prices

                        product_cards = []
                        best_deal_data = None

                        if isinstance(enhanced_results, list):
                            product_cards = enhanced_results
                            if product_cards:
                                best_deal_data = product_cards[0]
                        elif isinstance(enhanced_results, dict):
                            for key, value in enhanced_results.items():
                                if key.startswith("🏆"):
                                    best_deal_data = value if isinstance(value, dict) else None
                                    continue
                                if isinstance(value, dict):
                                    product_cards.append(value)
                                else:
                                    import re
                                    img_match = re.search(r'<img src="(.*?)"', str(value))
                                    link_match = re.search(r"\[Buy Now\]\((.*?)\)", str(value))
                                    price_match = re.search(r"₹[\d,.]+", str(value))
                                    rating_match = re.search(r"Rating.*?: ([\d.]+)", str(value))

                                    product_cards.append({
                                        'title': key.split(" - ", 1)[1] if " - " in key else key,
                                        'price': price_match.group(0) if price_match else "₹N/A",
                                        'rating': float(rating_match.group(1)) if rating_match else 4.0,
                                        'review_count': 100,
                                        'image': img_match.group(1) if img_match else "https://via.placeholder.com/150x150.png?text=No+Image",
                                        'link': link_match.group(1) if link_match else "#",
                                        'platform': 'default',
                                        'platform_name': 'Online Store',
                                        'delivery': 'Standard delivery',
                                        'savings': '',
                                        'extracted_quantity': '',
                                        'rank': len(product_cards) + 1
                                    })

                        if product_cards:
                            if best_deal_data:
                                banner_html = ComparisonTable.create_best_deal_banner(best_deal_data)
                                st.markdown(banner_html, unsafe_allow_html=True)
                            elif product_cards:
                                banner_html = ComparisonTable.create_best_deal_banner(product_cards[0])
                                st.markdown(banner_html, unsafe_allow_html=True)

                            product_cards_html = '<div class="product-container">'
                            for i, product_data in enumerate(product_cards):
                                card_html = ProductCard.create_card(product_data, i + 1)
                                product_cards_html += f'<div class="product-card">{card_html}</div>'
                            product_cards_html += '</div>'

                            st.markdown(product_cards_html, unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                        else:
                            st.warning("No products found matching your criteria. Try adjusting your search terms or quantity.")


# === Clear Session ===
if st.session_state.file_path:
    if st.button("🧹 Clear Session & Delete File"):
        try:
            os.remove(st.session_state.file_path)
            st.success(f"🗑 File deleted: {st.session_state.file_path}")
        except Exception as e:
            st.warning(f"Could not delete file: {e}")
        for key in ["file_path", "file_type", "timestamps", "summary", "file_base64"]:
            st.session_state[key] = None if key in ["file_path", "file_type"] else ""
