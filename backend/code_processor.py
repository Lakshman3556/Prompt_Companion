import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound


class CodeProcessor:
    """A class to handle code detection, formatting, and highlighting."""

    LANGUAGE_PATTERNS = {
        "python": {
            "keywords": [
                (r"\bdef\s+\w+\s*\(", 3),  # Function definition
                (r"\bclass\s+\w+\s*[:\(]", 3),  # Class definition
                (r"\bimport\s+\w+", 2),  # Import statement
                (r"\bfrom\s+\w+\s+import", 2),  # From import
                (r"@\w+", 1),  # Decorators
                (r"\basync\s+def", 3),  # Async function
                (r"\bawait\s+", 2),  # Await keyword
                (r":\s*$", 1),  # Line ending with colon
            ],
            "builtins": [
                r"print\s*\(",
                r"len\s*\(",
                r"range\s*\(",
                r"dict\s*\(",
                r"list\s*\(",
                r"set\s*\(",
            ],
        },
        "javascript": {
            "keywords": [
                (r"\bfunction\s+\w+\s*\(", 3),  # Function declaration
                (r"\bconst\s+\w+\s*=", 2),  # Const declaration
                (r"\blet\s+\w+\s*=", 2),  # Let declaration
                (r"\bvar\s+\w+\s*=", 1),  # Var declaration
                (r"=>", 2),  # Arrow function
                (r"\basync\s+function", 3),  # Async function
                (r"\bawait\s+", 2),  # Await keyword
                (r"\bconsole\.log\s*\(", 2),  # Console.log
            ]
        },
        "java": {
            "keywords": [
                (r"\bpublic\s+class\s+\w+", 3),  # Public class
                (r"\bprivate\s+\w+\s+\w+\s*\(", 2),  # Private method
                (r"\bprotected\s+\w+\s+\w+\s*\(", 2),  # Protected method
                (r"\bSystem\.out\.println\s*\(", 2),  # println
                (r"@Override", 2),  # Override annotation
                (r"\binterface\s+\w+", 2),  # Interface
            ]
        },
    }

    @staticmethod
    def detect_language(code):
        """Detect the programming language of a code snippet."""
        if not code.strip():
            return ""

        try:
            # Try to guess the lexer based on the code content
            lexer = guess_lexer(code)
            return lexer.aliases[0]
        except ClassNotFound:
            # Fall back to pattern matching if lexer guessing fails
            return CodeProcessor._detect_by_patterns(code)

    @staticmethod
    def _detect_by_patterns(code):
        """Detect language using regex patterns when lexer guessing fails."""
        scores = {}
        code_lines = code.split("\n")

        for lang, patterns in CodeProcessor.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern_type, pattern_list in patterns.items():
                if pattern_type == "keywords":
                    for pattern, weight in pattern_list:
                        for line in code_lines:
                            if re.search(pattern, line):
                                score += weight
                                break
                else:  # builtins and other patterns
                    for pattern in pattern_list:
                        for line in code_lines:
                            if re.search(pattern, line):
                                score += 1
                                break
            if score > 0:
                scores[lang] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return ""

    @staticmethod
    def format_code(code, language=""):
        """Format and clean up code while preserving indentation."""
        if not code.strip():
            return code

        # Detect language if not provided
        if not language:
            language = CodeProcessor.detect_language(code)

        # Remove unnecessary blank lines at start and end
        lines = code.split("\n")
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return ""

        # Find the minimum indentation level
        indentation = float("inf")
        for line in lines:
            if line.strip():  # Only consider non-empty lines
                current_indent = len(line) - len(line.lstrip())
                indentation = min(indentation, current_indent)

        # Remove the common indentation from all lines
        if indentation < float("inf"):
            formatted_lines = []
            for line in lines:
                if line.strip():  # Non-empty line
                    formatted_lines.append(line[indentation:])
                else:  # Empty line
                    formatted_lines.append("")

            code = "\n".join(formatted_lines)

        return code.strip()

    @staticmethod
    def highlight_code(code, language=""):
        """Highlight code using Pygments with fallback to plain text."""
        if not code.strip():
            return code

        try:
            # Try to get lexer for the specified language
            if language:
                lexer = get_lexer_by_name(language)
            else:
                # Try to guess the lexer based on content
                lexer = guess_lexer(code)

            # Create an HTML formatter with line numbers
            formatter = HtmlFormatter(
                style="monokai",
                linenos=True,
                cssclass="highlight",
                lineanchors="line",
                anchorlinenos=True,
                wrapcode=True,
            )

            # Highlight the code
            return highlight(code, lexer, formatter)
        except ClassNotFound:
            # Fallback to plain text if language detection fails
            return f'<pre class="highlight"><code>{code}</code></pre>'

    @staticmethod
    def get_css():
        """Get the CSS for syntax highlighting."""
        formatter = HtmlFormatter(style="monokai")
        return formatter.get_style_defs(".highlight")

    @staticmethod
    def format_response(text):
        """Format the entire response, processing both code blocks and text while preserving Markdown."""
        if not text:
            return ""

        def process_code_block(match):
            lang = match.group(1) or ""
            code = match.group(2)

            formatted_code = CodeProcessor.format_code(code, lang)

            if not lang:
                lang = CodeProcessor.detect_language(formatted_code)

            lang_display = lang.capitalize() if lang else "Code"
            return f"\n\n{lang_display}:\n\n{formatted_code}\n"

        # Process code blocks
        text = re.sub(
            r"```(\w+)?\n(.*?)\n```", process_code_block, text, flags=re.DOTALL
        )

        # Preserve Markdown formatting - do not strip * and # symbols
        # Keep paragraphs separated by blank lines
        # Ensure bullet points and headings are preserved

        return text.strip()
