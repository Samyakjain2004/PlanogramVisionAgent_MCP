import base64
import os
import cv2
import tempfile
from openai import AzureOpenAI
import time
from app.utils.product_extractor import extract_product_name
from dotenv import load_dotenv
load_dotenv()
import asyncio
import aiofiles
import cv2
import os
import tempfile
from functools import partial
from concurrent.futures import ThreadPoolExecutor
import tiktoken
import time
from collections import deque
import json

# Token and request rate limits
TOKENS_PER_MIN = 120_000
REQUESTS_PER_MIN = 1_200
ESTIMATED_TOKENS_PER_REQUEST = 1400  # Estimate: prompt + image + response

# Time window
WINDOW_SECONDS = 60
token_usage_log = deque()
request_log = deque()

def critic_validate_answer(user_question, direct_answer, reasoning, frame_analysis_text):
    critic_prompt = f"""
You are a Critic Agent that validates the accuracy of AI-generated responses in retail shelf image or video analysis.

Given:
- A user query
- The direct answer generated
- The reasoning provided
- Supporting evidence from multiple image frames

🎯 Tasks:
- Check if the direct answer is **factually supported** by any of the frame responses.
- Validate whether the reasoning logically follows from the visual evidence.
- Point out any incorrect or unsupported claims.
- If everything looks good, confirm the answer is accurate.

📌 User Question:
{user_question}

📍 Direct Answer:
{direct_answer}

🧠 Reasoning:
{reasoning}

🖼 Frame Analysis Evidence:
{frame_analysis_text}

✏️ Return output in the following format:

Critic Verdict: <Valid | Invalid>
Explanation: <what is accurate/inaccurate and why>
"""

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an expert QA critic evaluating factual correctness in AI responses."},
            {"role": "user", "content": critic_prompt}
        ],
        max_tokens=400,
        temperature=0.2,
        model=AZURE_OPENAI_DEPLOYMENT_NAME
    )

    return response.choices[0].message.content.strip()

async def rate_limited_call(func, *args, **kwargs):
    now = time.time()

    # Clear old entries
    while token_usage_log and now - token_usage_log[0][0] > WINDOW_SECONDS:
        token_usage_log.popleft()
    while request_log and now - request_log[0] > WINDOW_SECONDS:
        request_log.popleft()

    current_tokens = sum(tokens for _, tokens in token_usage_log)
    current_requests = len(request_log)

    # Print current load
    print(f"[📊] Current load: {current_requests} req/min, {current_tokens} tokens/min")

    if (current_tokens + ESTIMATED_TOKENS_PER_REQUEST > TOKENS_PER_MIN) or (current_requests >= REQUESTS_PER_MIN):
        wait_time = WINDOW_SECONDS - (now - request_log[0])
        wait_time = max(wait_time, 0.1)
        print(f"[⏳ Throttling] Waiting {wait_time:.2f}s to avoid exceeding limits...")
        await asyncio.sleep(wait_time)

    token_usage_log.append((time.time(), ESTIMATED_TOKENS_PER_REQUEST))
    request_log.append(time.time())
    print(f"[🚀] Making API request at {time.strftime('%H:%M:%S')}")
    return await func(*args, **kwargs)

def estimate_tokens(prompt: str, model="gpt-4"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

# Initialize client
client = AzureOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def classify_query_llm(user_query: str) -> str:
    system_prompt = "You are a query classification assistant. Classify the following retail video/image question into one of the following categories:\n" \
                    "- location_query\n- count_query\n- price_query\n- brand_query\n- product_identification\n- generic_query\n\nReturn ONLY the category name."

    user_prompt = f"Query: {user_query}\n\nCategory:"

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        max_tokens=10,
        temperature=0,
        top_p=1,
        timeout=10
    )

    return response.choices[0].message.content.strip().lower()

def extract_products_from_image(image_path, user_question, frame_number=None, fps=None, query_type="generic_query"):
    try:
        base64_image = encode_image(image_path)

        timestamp_ms = None
        if frame_number is not None and fps:
            timestamp_ms = int((frame_number / fps) * 1000)
            location_context = f"\n🖼 Frame Number: {frame_number}\n⏱ Timestamp (ms): {timestamp_ms}"
        else:
            location_context = ""
            
        # Check if API credentials are properly loaded
        if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, 
                   AZURE_OPENAI_API_VERSION, AZURE_OPENAI_API_KEY]):
            return "Error: Azure OpenAI API credentials are missing. Please check your .env file."

        prompt_text = f"""
You are a helpful assistant that analyzes retail shelf images taken from video frames. Each image is from a different time and angle in the store video. The user will ask a question about products on the shelf. Your job is to analyze **only this single image/frame**, and return a clear and factual answer.

🧠 General Instructions:
- Use only the visible contents of this frame to answer the user's question.
- Frame context: {location_context}
- Do not assume what's outside the frame or in other frames.
- Be concise, courteous, and specific to the query.
- If the requested product or detail is **not visible**, state that clearly.
- If the query refers to a **specific product**, then at the end of the summary add a new line in this format exactly:
  `product_name = <Product Name>`
- If no product is mentioned, skip this line.
- Always end your response with: `product_name = <Product Name>` if a product is clearly referenced or visible.


Query Type: {query_type}
User Query: {user_question}
"""
        # if query_type == "location_query":
        #     prompt_text += "\nFocus on where the product is placed or visible in the frame."
        # elif query_type == "count_query":
        #     prompt_text += "\nTry to count the number of visible products."
        # elif query_type == "price_query":
        #     prompt_text += "\nLook for visible price tags or labels."
        # elif query_type == "brand_query":
        #     prompt_text += "\nIdentify the product's brand if visible."
        # elif query_type == "product_identification":
        #     prompt_text += "\nIdentify what product is shown in the frame."
        # else:
        #     prompt_text += "\nAnswer clearly based on what’s visible."
        if query_type == "location_query":
            prompt_text += """
        Focus on where the product is placed or visible in the frame.

        Return your answer in a complete sentence using the format below:
        
        Direct Answer: <short sentence describing the product's location>
        Reasoning: <brief explanation based on visual observation>"""



        elif query_type == "count_query":

            prompt_text += """

        If the user is asking what percentage of shelf space each product occupies, estimate approximate percentages based on visual size and presence on the shelf.


        Return your answer in the following format exactly:


        Direct Answer: <Give direct or range of percentage for the product asked or about whatever percentage is asked based on image content only>

        Reasoning: <brief explanation based on the image content>

        """

        elif query_type == "price_query":
            prompt_text += """
        Look for visible price tags, price boards, or labels in the frame.

        If the price is not clearly visible, return a sentence like "The price is not visible in this frame."

        Return your answer in the following format exactly:

        Direct Answer: <price or a full sentence like "The price is not visible.">
        Reasoning: <explain how the price was identified or why it’s not visible>"""

        elif query_type == "brand_query":
            prompt_text += """
        Identify the brand of the product(s) visible in the frame.

        If no brand is clearly identifiable, return a full sentence like "The brand is not visible in the image."

        Return your answer in the following format exactly:

        Direct Answer: <brand name or a sentence like "Brand not visible in the image.">
        Reasoning: <explanation based on product packaging, logo, or label clues>"""

        elif query_type == "product_identification":
            prompt_text += """
        Identify the product shown in the frame based on visual appearance.

        If no product is clearly identifiable, return a full sentence like "The product is not recognizable in this image."

        Return your answer in the following format exactly:

        Direct Answer: <product name or full sentence>
        Reasoning: <why you think it is this product (e.g., color, label, logo)>"""

        else:  # generic_query or fallback
            prompt_text += """
        Answer the user's question clearly based on what is visible in the frame.

        Avoid single-word answers like just "Yes" or "No". Use a complete sentence to answer, even if it's a simple one.

        Return your answer in the following format exactly:

        Direct Answer: <your best complete answer>
        Reasoning: <brief explanation based on the image content>"""

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert retail shelf analyst that provides accurate, image-based product insights from shelf photos."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2048,
            temperature=0.1,
            top_p=1.0,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            timeout=30  # Add 30 second timeout to prevent hanging
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        error_type = str(type(e).__name__)
        error_message = str(e)
        
        # More specific error handling
        if "timeout" in error_message.lower():
            print(f"[⚠️ Skipping frame {frame_number} due to error: Request timed out.]")
            return f"[Skipped frame {frame_number} due to timeout. Try again later.]"
        elif any(net_err in error_message.lower() for net_err in ["connection", "network", "connect"]):
            print(f"[⚠️ Skipping frame {frame_number} due to error: Connection error.]")
            return f"[Skipped frame {frame_number} due to connection error. Check your internet connection.]"
        else:
            print(f"[⚠️ Skipping frame {frame_number} due to error: {error_type}: {error_message}]")
            return f"[Skipped frame {frame_number} due to error: {error_type}]"


MAX_CONCURRENT_TASKS = 30
executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)

async def async_extract_products(image_path, user_question, frame_number, fps, query_type):
    loop = asyncio.get_event_loop()
    return await rate_limited_call(
        loop.run_in_executor,
        executor,
        partial(
            extract_products_from_image,
            image_path=image_path,
            user_question=user_question,
            frame_number=frame_number,
            fps=fps,
            query_type=query_type
        )
    )

def get_total_tokens(prompt: str, response: str = "", model="gpt-4o"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt)) + len(enc.encode(response))

async def process_frame(frame, frame_index, fps, user_question, semaphore, query_type):
    async with semaphore:
        # Save frame to temp file asynchronously
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        filename = temp_file.name
        temp_file.close()

        cv2.imwrite(filename, frame)  # Still uses OpenCV (blocking)

        timestamp_ms = int((frame_index / fps) * 1000)

        try:
            response = await async_extract_products(
                filename, user_question, frame_index, fps, query_type
            )
        finally:
            os.remove(filename)

        return {
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms,
            "response": response
        }

async def analyze_video_for_query_async(video_path, user_question, frame_interval=23):
    # 🔍 Step 1: Classify the query using LLM
    query_type = classify_query_llm(user_question)
    print(f"[🔎 Query classified as]: {query_type}")
    # ✅ If the input is an image, run image-only analysis
    # if video_path.lower().endswith((".jpg", ".jpeg", ".png")):
    #     print("[🖼 Detected image file — using image processing pipeline]")
    #     response = extract_products_from_image(
    #         image_path=video_path,
    #         user_question=user_question,
    #         query_type=query_type
    #     )
    #     product_name = extract_product_name(response)
    #     if not product_name or product_name.lower() == "unknown":
    #         product_name = extract_product_name(user_question)
    #     return {
    #         "final_summary": response,
    #         "timestamps": [],
    #         "product_name": product_name
    #     }
    if video_path.lower().endswith((".jpg", ".jpeg", ".png")):
        print("[🖼 Detected image file — using image processing pipeline]")
        response = extract_products_from_image(
            image_path=video_path,
            user_question=user_question,
            query_type=query_type
        )

        direct_answer = ""
        reasoning = ""
        product_name = "Unknown"

        for line in response.splitlines():
            lower_line = line.lower()
            if lower_line.startswith("direct answer:"):
                direct_answer = line.partition(":")[2].strip()
            elif lower_line.startswith("reasoning:"):
                reasoning = line.partition(":")[2].strip()
            elif lower_line.startswith("product_name ="):
                product_name = line.partition("=")[2].strip()

        # Final fallback logic
        if not product_name or product_name.lower() == "unknown":
            product_name = extract_product_name(direct_answer or user_question or reasoning)

        result = {
            "direct_answer": direct_answer,
            "reasoning": reasoning if reasoning else response,
            "timestamps": [],
            "product_name": product_name
        }

        print("[📸 JSON Output from Image]:")
        print(json.dumps(result, indent=4))

        return result

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    tasks = []
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            task = asyncio.create_task(
                process_frame(frame, frame_index, fps, user_question, semaphore, query_type)
            )
            tasks.append(task)

        frame_index += 1

    cap.release()
    results = await asyncio.gather(*tasks)

    frame_responses = []
    product_timestamps = []

    video_duration_ms = (total_frames / fps) * 1000
    end_threshold_ms = video_duration_ms * 0.9

    for result in results:
        frame_index = result["frame_index"]
        timestamp_ms = result["timestamp_ms"]
        response = result["response"]

        frame_responses.append(f"🖼 Frame {frame_index} ({timestamp_ms} ms):\n{response}")

        response_clean = response.lower()
        keywords_present = any(k in response_clean for k in [
            "located", "visible", "is on", "can be seen", "placed", "sitting", "present", "seen"
        ])
        uncertain = any(p in response_clean for p in [
            "not visible", "not found", "unclear", "could be", "might be", "probably"
        ])

        if keywords_present and not uncertain:
            if timestamp_ms < end_threshold_ms or "end" not in response_clean:
                product_timestamps.append(timestamp_ms)

    # Remove frame numbers like "🖼 Frame 23 (4500 ms):" before summary
    cleaned_frame_responses = []
    for line in frame_responses:
        parts = line.split(":\n", 1)
        if len(parts) == 2:
            cleaned_frame_responses.append(parts[1].strip())
        else:
            cleaned_frame_responses.append(line.strip())
    combined_text = "\n\n".join(cleaned_frame_responses)

    # Call final summarizer (keep synchronous)
    summary_prompt = f"""
You are a summarization assistant. Based on the following frame-wise analysis of a shelf video, identify and answer the user's question directly and explain your reasoning clearly.

User Query: {user_question}

🔍 Frame Responses:
{combined_text}
✏️ Return in the following format:
Direct Answer: <your direct answer here>
Reasoning: <brief but clear reasoning for your answer>
✏️ Return a helpful, natural language summary. End with:
product_name = <Product Name> (if mentioned)
"""
    summary_response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a summarization expert for retail shelf video analytics."},
            {"role": "user", "content": summary_prompt}
        ],
        max_tokens=512,
        temperature=0.3,
        top_p=1.0,
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        timeout=30
    )
    response_text = summary_response.choices[0].message.content.strip()

    # Simple parsing assuming format:
    # Direct Answer: ...
    # Reasoning: ...
    direct_answer = ""
    reasoning = ""

    for line in response_text.splitlines():
        if line.lower().startswith("direct answer:"):
            direct_answer = line.partition(":")[2].strip()
        elif line.lower().startswith("reasoning:"):
            reasoning = line.partition(":")[2].strip()

    # Fallback if direct answer is still not parsed
    if not direct_answer:
        direct_answer = extract_product_name(response_text)
    if not reasoning:
        reasoning = response_text  # fallback to whole text

    product_name = extract_product_name(direct_answer or user_question)

    # base_summary = summary_response.choices[0].message.content.strip()
    # product_name = extract_product_name(base_summary)
    # if not product_name or product_name.lower() == "unknown":
    #     product_name = extract_product_name(user_question)
    #
    # return {
    #     "final_summary": base_summary,
    #     "timestamps": product_timestamps,
    #     "product_name": product_name
    # }
    base_summary = summary_response.choices[0].message.content.strip()
    product_name = extract_product_name(base_summary)
    if not product_name or product_name.lower() == "unknown":
        product_name = extract_product_name(user_question)

    result = {
        "direct_answer": direct_answer,
        "reasoning": reasoning,
        "timestamps": product_timestamps,
        "product_name": product_name
    }
    # --- Critic Evaluation ---
    critic_feedback = critic_validate_answer(
        user_question=user_question,
        direct_answer=direct_answer,
        reasoning=reasoning,
        frame_analysis_text=combined_text
    )

    result["critic_feedback"] = critic_feedback

    print("[📦 JSON Output]:")
    print(json.dumps(result, indent=4))

    return result


def analyze_video_for_query(video_path, user_question, frame_interval=23):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_responses = []
    product_timestamps = []
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_image_file:
                temp_filename = temp_image_file.name
                cv2.imwrite(temp_filename, frame)

            timestamp_ms = int((frame_index / fps) * 1000)

            response = extract_products_from_image(
                image_path=temp_filename,
                user_question=user_question,
                frame_number=frame_index,
                fps=fps
            )

            frame_responses.append(f"🖼 Frame {frame_index} ({timestamp_ms} ms):\n{response}")

            # if "not visible" not in response.lower() and "not found" not in response.lower():
            #     product_timestamps.append(timestamp_ms)
            # === Heuristics to detect valid frames ===
            response_clean = response.lower()

            # Only include confident detections
            keywords_present = any(keyword in response_clean for keyword in
                                   ["located", "visible", "is on", "can be seen", "placed", "sitting", "present",
                                    "seen"])
            uncertain_phrases = any(phrase in response_clean for phrase in
                                    ["not visible", "not found", "unclear", "could be", "might be", "probably"])

            # Skip last few frames if likely false positive
            video_duration_ms = (total_frames / fps) * 1000
            end_threshold_ms = video_duration_ms * 0.9  # last 10%

            if keywords_present and not uncertain_phrases:
                if timestamp_ms < end_threshold_ms or "end" not in response_clean:
                    product_timestamps.append(timestamp_ms)

            os.remove(temp_filename)

        frame_index += 1

    cap.release()

    combined_text = "\n\n".join(frame_responses)

    summary_prompt = f"""
You are a summarization assistant. Based on the following frame-wise analysis of a shelf video, write a summary of where the requested product(s) appear.
- If the query refers to a **specific product**, then at the end of the summary add a new line in this format exactly:
  `product_name = <Product Name>`
- If no product is mentioned, skip this line.

Return ONLY the summary and the product name line if applicable.

📌 User Query: {user_question}

🔍 Frame Responses:
{combined_text}

✏️ Return a helpful, natural language summary for the user. Do not include any extra information (about frames and frame numbers) other than the answer to the asked query.
"""

    summary_response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a summarization expert for retail shelf video analytics."},
            {"role": "user", "content": summary_prompt}
        ],
        max_tokens=512,
        temperature=0.3,
        top_p=1.0,
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        timeout=30  # Add 30 second timeout to prevent hanging
    )

    base_summary = summary_response.choices[0].message.content.strip()

    # Final return: summary without timestamps, but timestamps available separately
    if not product_timestamps or "not visible" in base_summary.lower():
        product_timestamps = []
    if video_path.lower().endswith((".jpg", ".jpeg", ".png")):
        response = extract_products_from_image(image_path=video_path, user_question=user_question)
        evaluation_result = evaluate_summary_accuracy(user_question, base_summary, combined_text)
        print("\n--- Evaluation Summary ---")
        print(evaluation_result)
        product_name = extract_product_name(base_summary)
        if not product_name or product_name.lower() == "unknown":
            product_name = extract_product_name(user_question)
        print(f"[🛍️ Extracted Product Name]: {product_name}")
        return {
            "final_summary": base_summary,
            "timestamps": product_timestamps,
            "product_name": product_name
        }
    evaluation_result = evaluate_summary_accuracy(user_question, base_summary, combined_text)
    print("\n--- Evaluation Summary ---")
    print(evaluation_result)
    product_name = extract_product_name(base_summary)
    if not product_name or product_name.lower() == "unknown":
        product_name = extract_product_name(user_question)
    print(f"[🛍️ Extracted Product Name]: {product_name}")
    return {
        "final_summary": base_summary,
        "timestamps": product_timestamps,
        "product_name": product_name
    }

def evaluate_summary_accuracy(user_question, generated_summary, frame_analysis_text):
    evaluation_prompt = f"""
You are an evaluation assistant. Your job is to evaluate the quality of the generated summary based on the provided supporting frame analysis.

🧠 Guidelines:
- The frame responses may each contain partial or new information.
- The final summary is expected to combine this information holistically.
- Do NOT compare each line of the summary with each frame.
- Instead, check if the facts stated in the summary are **generally supported** by at least one of the frames.
- The summary should not contradict the evidence.
- Do NOT penalize the summary for not including every frame.
- Only judge whether the included information is accurate and relevant to the user's question.

🧪 Additional Rule:
- If the summary is **not 100% accurate**, list exactly what information is **incorrect**, **unsupported**, or **missing** based on the frame responses.

📌 User Question:
{user_question}

📄 Generated Summary:
{generated_summary}

📷 Supporting Frame Responses:
{frame_analysis_text}

🎯 Please return your evaluation in the following format:

Accuracy Score (0–100)%: <score>
Evaluation Summary: <brief explanation of factual correctness and completeness>
"""

    eval_response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an unbiased evaluator that assesses summary quality based on provided evidence."},
            {"role": "user", "content": evaluation_prompt}
        ],
        max_tokens=300,
        temperature=0.2,
        model=AZURE_OPENAI_DEPLOYMENT_NAME  # Or use "gpt-4o" if preferred
    )

    return eval_response.choices[0].message.content.strip()
