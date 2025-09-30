import os
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Gemini API config ---
API_KEY = os.getenv("OPENAI_KEY")  # Add this in Cloud Run environment variables
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent?key="

# --- Product reference images ---
PRODUCT_MAP = {
    "cup": "static/cup.jpeg",
    "bag": "static/paper_bag.jpeg",
    "paper_bowl": "static/paper_bowl.jpeg",
    "white_cup": "static/white_cup.jpeg",
    "meal_box": "static/meal_box.jpeg",
    "napkin": "static/napkin.jpeg",
    "wrapping_paper": "static/wrapping_paper.jpeg"
}

# --- Default prompt ---
DEFAULT_PROMPT = "Blend the logo onto this product. Ensure realistic lighting, shadows, texture, and make background suitable."

@app.route("/generate-mockup-gemini", methods=["POST"])
def generate_mockup():
    try:
        data = request.get_json()
        product_name = data.get("product_name")
        logo_b64 = data.get("logo_b64")
        extra_text = data.get("extra_text", "").strip()

        if not product_name or not logo_b64:
            return jsonify({"error": "Missing product name or logo"}), 400

        product_path = PRODUCT_MAP.get(product_name)
        if not product_path:
            return jsonify({"error": "Invalid product"}), 400

        # Read product image
        with open(product_path, "rb") as f:
            product_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Construct prompt
        prompt_text = extra_text if extra_text else DEFAULT_PROMPT

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {"inlineData": {"mimeType": "image/jpeg", "data": product_b64}},
                        {"inlineData": {"mimeType": "image/png", "data": logo_b64}}
                    ]
                }
            ],
            "generationConfig": {"responseModalities": ["IMAGE"]}
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{API_URL}{API_KEY}", json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        img_b64 = result.get("candidates")[0]["content"]["parts"][0]["inlineData"]["data"]

        return jsonify({"image_b64": img_b64})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

# Health check
@app.route("/")
def home():
    return "Mockup backend running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
