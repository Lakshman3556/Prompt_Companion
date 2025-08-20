import React, { useState, useEffect } from 'react';
import './syntax-highlight.css';

const examplePrompts = [
  { text: "Can you summarize this article for me?", category: "summarization" },
  { text: "Help me fix this Python code", category: "code help" },
  { text: "Check my grammar in this sentence", category: "grammar check" },
  { text: "What do you think about AI?", category: "general" }
];

const categoryColors = {
  summarization: '#4CAF50',
  'code help': '#2196F3',
  'grammar check': '#9C27B0',
  general: '#FF9800'
};

function App() {
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('http://localhost:5000/api/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });

      if (!res.ok) {
        throw new Error('Failed to get response');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError('Failed to connect to the server. Make sure the backend is running!');
    } finally {
      setIsLoading(false);
    }
  };

  const tryExample = (examplePrompt) => {
    setPrompt(examplePrompt);
  };

  // Function to copy code to clipboard
  const copyToClipboard = async (code) => {
    try {
      await navigator.clipboard.writeText(code);
      // You could add a visual feedback here
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  // Function to safely parse and render HTML content
  const renderContent = (content) => {
    // If the content doesn't contain HTML (Pygments output), return it as is
    if (!content.includes('class="highlight"')) {
      return content;
    }

    return (
      <div
        dangerouslySetInnerHTML={{
          __html: content
        }}
        onClick={(e) => {
          // Handle copy button clicks
          if (e.target.classList.contains('copy-button')) {
            const codeBlock = e.target.closest('.code-block');
            const code = codeBlock.querySelector('pre').textContent;
            copyToClipboard(code);
            
            // Visual feedback
            e.target.textContent = 'Copied!';
            setTimeout(() => {
              e.target.textContent = 'Copy';
            }, 2000);
          }
        }}
      />
    );
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Prompt Companion</h1>
      <p style={styles.subtitle}>Your AI companion for various text-based tasks</p>

      <div style={styles.examplesContainer}>
        <h3 style={styles.examplesTitle}>Try these examples:</h3>
        <div style={styles.examples}>
          {examplePrompts.map((example, index) => (
            <button
              key={index}
              onClick={() => tryExample(example.text)}
              style={{
                ...styles.exampleButton,
                backgroundColor: categoryColors[example.category]
              }}
            >
              {example.text}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.inputContainer}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt..."
            style={styles.input}
            rows={4}
          />
          <button 
            type="submit" 
            style={styles.submitButton}
            disabled={isLoading || !prompt.trim()}
          >
            {isLoading ? 'Processing...' : 'Send'}
          </button>
        </div>
      </form>

      {error && (
        <div style={styles.error}>
          {error}
        </div>
      )}

      {result && (
        <div style={styles.result}>
          <div style={{
            ...styles.categoryBadge,
            backgroundColor: categoryColors[result.category]
          }}>
            {result.category.toUpperCase()}
          </div>
          <div style={styles.response}>
            {renderContent(result.response)}
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  },
  title: {
    textAlign: 'center',
    color: '#1a73e8',
    marginBottom: '10px',
  },
  subtitle: {
    textAlign: 'center',
    color: '#5f6368',
    marginBottom: '30px',
  },
  form: {
    marginBottom: '30px',
  },
  inputContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  input: {
    padding: '15px',
    fontSize: '16px',
    border: '2px solid #e0e0e0',
    borderRadius: '8px',
    resize: 'vertical',
    minHeight: '100px',
    fontFamily: 'inherit',
  },
  submitButton: {
    padding: '12px 24px',
    fontSize: '16px',
    backgroundColor: '#1a73e8',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    ':hover': {
      backgroundColor: '#1557b0',
    },
    ':disabled': {
      backgroundColor: '#ccc',
      cursor: 'not-allowed',
    },
  },
  result: {
    backgroundColor: '#f8f9fa',
    padding: '20px',
    borderRadius: '8px',
    marginTop: '20px',
  },
  categoryBadge: {
    display: 'inline-block',
    padding: '6px 12px',
    borderRadius: '16px',
    color: 'white',
    fontSize: '14px',
    fontWeight: 'bold',
    marginBottom: '10px',
  },
  response: {
    margin: '0',
    fontSize: '16px',
    lineHeight: '1.6',
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '15px',
    borderRadius: '8px',
    marginBottom: '20px',
  },
  examplesContainer: {
    marginBottom: '30px',
  },
  examplesTitle: {
    color: '#5f6368',
    marginBottom: '10px',
  },
  examples: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
  },
  exampleButton: {
    padding: '8px 16px',
    fontSize: '14px',
    color: 'white',
    border: 'none',
    borderRadius: '16px',
    cursor: 'pointer',
    transition: 'opacity 0.2s',
    ':hover': {
      opacity: 0.9,
    },
  },
};

export default App;
