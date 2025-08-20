from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def categorize_prompt(prompt):
    prompt_lower = prompt.lower()
    if "summarize" in prompt_lower:
        return "summarization", "Here’s a short summary of your text."
    elif "code" in prompt_lower:
        return "code help", "Looks like you need coding assistance."
    elif "grammar" in prompt_lower:
        return "grammar check", "I fixed the grammar issues in your text."
    else:
        return "general", "I’m not sure, but here’s my response."

@app.route("/api/prompt", methods=["POST"])
def handle_prompt():
    data = request.json
    user_prompt = data.get("prompt", "")
    
    category, response = categorize_prompt(user_prompt)
    
    return jsonify({
        "category": category,
        "response": response
    })

if __name__ == "__main__":
    app.run(debug=True)
