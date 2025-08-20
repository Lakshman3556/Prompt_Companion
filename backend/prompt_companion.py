import sys
import re
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
from code_processor import CodeProcessor

# Load environment variables
load_dotenv()

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please add your API key.")

try:
    genai.configure(api_key=GOOGLE_API_KEY)

    model = genai.GenerativeModel("models/gemini-2.5-pro")
    # Test the API connection
    test_response = model.generate_content("Hello")
    print("Successfully connected to Gemini AI API")
except Exception as e:
    print(f"Error configuring Gemini AI: {str(e)}")
    print("Please check your API key and internet connection")
    sys.exit(1)

app = Flask(__name__)
CORS(app)


def categorize_prompt(prompt):
    """
    Categorize the user's prompt into one of four categories based on keywords.
    Returns both the category and a simulated response.
    """
    prompt_lower = prompt.lower()

    # Keywords for each category
    summarization_keywords = {
        "summarize",
        "summary",
        "tldr",
        "tl;dr",
        "explain briefly",
        "in short",
    }
    code_keywords = {
        "code",
        "program",
        "function",
        "python",
        "javascript",
        "java",
        "error",
        "bug",
        "syntax",
        "how to",
    }
    grammar_keywords = {"grammar", "spell", "correct", "proofread", "edit", "writing"}

    # Check for summarization request
    if any(keyword in prompt_lower for keyword in summarization_keywords):
        return "summarization", generate_summary_response(prompt)

    # Check for code help request
    elif any(keyword in prompt_lower for keyword in code_keywords):
        return "code_help", generate_code_response(prompt)

    # Check for grammar check request
    elif any(keyword in prompt_lower for keyword in grammar_keywords):
        return "grammar_check", generate_grammar_response(prompt)

    # Default to general category
    else:
        return "general", generate_general_response(prompt)


def format_response(text):
    """Clean and format the response text while preserving code blocks."""
    return CodeProcessor.format_response(text)


def detect_code_language(code):
    """Detect the programming language of a code snippet."""
    return CodeProcessor.detect_language(code)


def enhance_prompt(category, prompt):
    """Add context and instructions to the prompt for better responses."""
    if category == "summary":
        return (
            "Please provide a clear and concise summary of the following text. "
            "Focus on the main points and key takeaways. Avoid using markdown or special formatting. "
            f"Here's the text to summarize: {prompt}"
        )
    return prompt


def generate_summary_response(prompt):
    """Generate a summary response using Gemini AI."""
    if not prompt.strip():
        return "Please provide some text to summarize."

    try:
        # Create an enhanced prompt that encourages structured output
        enhanced_prompt = (
            "Please provide a clear and concise summary of the following text. "
            "Format your response as follows:\n"
            "1. Start with a brief overview (2-3 sentences)\n"
            "2. List the main points using bullet points\n"
            "3. If there are any key statistics or dates, highlight them\n"
            "4. End with a one-sentence conclusion\n\n"
            f"Here's the text to summarize:\n\n{prompt}"
        )

        response = model.generate_content(enhanced_prompt)

        if not response.text or response.text.strip() == "":
            raise ValueError("Empty response received from API")

        # Process the response through our formatter
        formatted_response = format_response(response.text)

        # If the response doesn't contain proper formatting, add it
        if "•" not in formatted_response and "*" not in formatted_response:
            lines = formatted_response.split("\n")
            if len(lines) > 1:
                # Convert plain text paragraphs into a structured format
                formatted_lines = []
                for i, line in enumerate(lines):
                    if line.strip():
                        if i == 0:
                            formatted_lines.append("Overview:\n" + line)
                        elif i == len(lines) - 1:
                            formatted_lines.append("\nConclusion:\n" + line)
                        else:
                            formatted_lines.append("• " + line)
                formatted_response = "\n".join(formatted_lines)

        return formatted_response

    except Exception as e:
        error_msg = str(e)
        print(f"Error generating summary: {error_msg}")

        if "quota" in error_msg.lower():
            return (
                "API quota exceeded. Please try again later or check your API limits."
            )
        elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
            return "Invalid API key. Please check your API key configuration."
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            return "Network error occurred. Please check your internet connection and try again."
        else:
            return (
                "I apologize, but I encountered an error while generating the summary. "
                "This might be because:\n"
                "1. The text is too long or complex\n"
                "2. There was an issue processing the formatting\n"
                "3. The API is currently experiencing issues\n\n"
                "Please try with a shorter text or try again in a moment."
            )


def generate_code_response(prompt):
    """Generate a code-related response using Gemini AI."""
    language = detect_programming_language(prompt)

    # Enhance the prompt with more specific error handling context if it looks like an error question
    if (
        "error" in prompt.lower()
        or "wrong" in prompt.lower()
        or "fix" in prompt.lower()
    ):
        code_prompt = (
            f"You are a programming expert helping debug code {'in ' + language if language else ''}. "
            "Follow these guidelines for your response:\n"
            "1. Clearly explain what might be causing the error or issue\n"
            "2. Show both the problematic code and the corrected code in separate blocks\n"
            "3. Explain each fix and why it resolves the issue\n"
            "4. Add comments to highlight the key changes\n"
            "5. Provide any relevant best practices or tips to avoid similar issues\n\n"
            f"Here's the question about the code issue: {prompt}"
        )
    else:
        code_prompt = (
            f"You are a programming expert {'working with ' + language if language else ''}. "
            "Follow these guidelines for your response:\n"
            "1. Start with a clear explanation in natural language\n"
            "2. When showing code examples:\n"
            "   - Use markdown code blocks with appropriate language tags\n"
            "   - Ensure consistent indentation (use spaces, not tabs)\n"
            "   - Add comments to explain complex parts\n"
            "   - Follow standard coding style for the language\n"
            "3. After the code, explain how it works\n\n"
            f"Here's their question: {prompt}"
        )

    try:
        response = model.generate_content(code_prompt)

        if not response.text or response.text.strip() == "":
            raise ValueError("Empty response received from API")

        # Let the CodeProcessor handle the formatting with syntax highlighting
        formatted_response = format_response(response.text)

        # Validate the response contains code blocks
        if "```" not in formatted_response:
            # If no code blocks found in a code help response, that's probably an error
            raise ValueError("Response doesn't contain any code examples")

        return formatted_response
    except Exception as e:
        error_msg = str(e)
        print(f"Error generating code response: {error_msg}")

        if "quota" in error_msg.lower():
            return (
                "API quota exceeded. Please try again later or check your API limits."
            )
        elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
            return "Invalid API key. Please check your API key configuration."
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            return "Network error occurred. Please check your internet connection and try again."
        else:
            return (
                "I apologize, but I encountered an error while processing your code question. "
                "This might be because:\n"
                "1. The code snippet is incomplete or unclear\n"
                "2. There was an issue understanding the specific error you're encountering\n"
                "3. The API is currently experiencing issues\n\n"
                "Please try rephrasing your question with more details about the code and any "
                "specific errors you're seeing."
            )


def generate_grammar_response(prompt):
    """Generate a grammar-related response using Gemini AI."""
    grammar_prompt = (
        "As a grammar and writing expert, please analyze the following text. "
        "Provide your response in clear, natural language with specific suggestions "
        "and explanations. Avoid using special formatting or symbols. "
        f"Here's the text to check: {prompt}"
    )
    try:
        response = model.generate_content(grammar_prompt)
        formatted_response = format_response(response.text)
        return formatted_response
    except Exception as e:
        print(f"Error generating grammar response: {str(e)}")
        return "I apologize, but I encountered an error while checking the grammar. Please try again."


def generate_general_response(prompt):
    """Generate a general response using Gemini AI."""
    enhanced_prompt = (
        "Please provide a clear and helpful response to this question. "
        "Use natural language and avoid special formatting or symbols. "
        f"Here's the question: {prompt}"
    )
    try:
        response = model.generate_content(enhanced_prompt)
        formatted_response = format_response(response.text)
        return formatted_response
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "I apologize, but I encountered an error while generating a response. Please try again."


def detect_programming_language(prompt):
    """Detect programming language mentioned in the prompt."""
    languages = {
        "python": "Python",
        "javascript": "JavaScript",
        "java": "Java",
        "c\\+\\+": "C++",
        "typescript": "TypeScript",
        "ruby": "Ruby",
        "php": "PHP",
    }

    for pattern, language in languages.items():
        if re.search(pattern, prompt.lower()):
            return language
    return None


@app.route("/api/prompt", methods=["POST"])
def handle_prompt():
    """Handle API requests for prompt processing."""
    data = request.json
    user_prompt = data.get("prompt", "")

    category, response = categorize_prompt(user_prompt)

    return jsonify({"category": category, "response": response})


def cli_mode():
    """Run the program in CLI mode."""
    print("Welcome to Prompt Companion Tool!")
    print("Type 'exit' or 'quit' to end the session.")
    print("-" * 50)

    while True:
        try:
            # Get user input
            user_input = input("\nEnter your prompt: ").strip()

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                print("\nThank you for using Prompt Companion Tool!")
                break

            # Process the prompt
            category, response = categorize_prompt(user_input)

            # Display the response
            print("\nCategory:", category.upper())
            print("Response:", response)
            print("-" * 50)

        except KeyboardInterrupt:
            print("\n\nExiting Prompt Companion Tool...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try again.")


if __name__ == "__main__":
    # If no arguments provided, run in CLI mode
    if len(sys.argv) == 1:
        cli_mode()
    # If --server argument is provided, run the Flask server
    elif len(sys.argv) > 1 and sys.argv[1] == "--server":
        app.run(debug=True)
    else:
        print(
            "Invalid argument. Use --server to run in server mode, or no arguments for CLI mode."
        )
