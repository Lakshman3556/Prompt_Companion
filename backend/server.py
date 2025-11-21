import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Import your existing logic exactly as-is
# (DO NOT CHANGE ANYTHING in prompt_companion.py)
from prompt_companion import classify_section, format_response

# Load .env (backend/.env)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Fetch API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add your API key.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Force stable FREE model to avoid quota issues
MODEL_NAME = "gemini-2.0-flash"
model = genai.GenerativeModel(MODEL_NAME)

# Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


@app.route("/api/ask", methods=["POST"])
def handle_ask():
    try:
        data = request.json
        if not data or "prompt" not in data:
            return jsonify({"error": "Missing 'prompt'"}), 400

        user_prompt = data["prompt"].strip()
        if not user_prompt:
            return jsonify({"error": "Prompt cannot be empty"}), 400

        current_section = data.get("current_section")

        # --- Use EXISTING classsifier (your logic unchanged) ---
        detected_section = classify_section(user_prompt, model)

        # Global personality instruction (unchanged)
        personality_instruction = (
            "You are a friendly, funny, interactive AI assistant. Be helpful, "
            "structured, clear, formatted, and mildly humorous. Use clean Markdown: "
            "paragraphs, blank lines, bullets, numbered lists, headings, bold/italic."
        )

        section_instructions = {
            "health": "You are a health expert. Answer only in health context.",
            "banking": "You are a finance expert. Answer only in banking context.",
            "movies": "You are a movie expert. Answer only in cinema context.",
            "music": "You are a music expert. Answer only in music context.",
            "general": "You are a general-purpose AI assistant.",
        }

        system_instruction = (
            personality_instruction
            + "\n\n"
            + section_instructions.get(
                detected_section, section_instructions["general"]
            )
        )

        enhanced_prompt = f"{system_instruction}\n\nUser question: {user_prompt}"

        # Generate AI response
        ai_response = model.generate_content(enhanced_prompt)

        # --- Use EXISTING formatter (your logic unchanged) ---
        final_output = format_response(ai_response.text)

        response_data = {"response": final_output}

        # Check for auto section switching
        if current_section and detected_section != current_section:
            response_data["redirect"] = True
            response_data["section"] = detected_section

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
