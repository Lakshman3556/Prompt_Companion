import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Copy, Download, Trash2 } from 'lucide-react';
import jsPDF from 'jspdf';
import './syntax-highlight.css';

const sections = [
  { id: 'health', name: 'Health', color: 'bg-green-500', examples: ['How to boost immunity?', 'Best exercises for beginners', 'Healthy meal ideas'] },
  { id: 'banking', name: 'Banking', color: 'bg-yellow-500', examples: ['Investment tips', 'Credit card advice', 'Saving strategies'] },
  { id: 'general', name: 'General', color: 'bg-blue-500', examples: ['Explain quantum physics', 'Travel recommendations', 'Cooking tips'] },
  { id: 'movies', name: 'Movies', color: 'bg-purple-500', examples: ['Best sci-fi movies', 'Movie recommendations', 'Film analysis'] },
  { id: 'music', name: 'Music', color: 'bg-pink-500', examples: ['Music recommendations', 'Artist analysis', 'Genre exploration'] }
];

function App() {
  const [currentSection, setCurrentSection] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const [theme, setTheme] = useState('dark');
  const [chatHistory, setChatHistory] = useState({});
  const [isTyping, setIsTyping] = useState(false);

  // Load saved data on mount
  useEffect(() => {
    const savedSection = localStorage.getItem('currentSection');
    const savedChat = localStorage.getItem('chatHistory');

    if (savedSection) {
      const section = sections.find(s => s.id === savedSection);
      if (section) setCurrentSection(section);
    }
    if (savedChat) {
      const parsedHistory = JSON.parse(savedChat);
      // Filter out removed sections from chat history
      const filteredHistory = {};
      sections.forEach(sec => {
        if (parsedHistory[sec.id]) {
          filteredHistory[sec.id] = parsedHistory[sec.id];
        }
      });
      setChatHistory(filteredHistory);
    }
  }, []);

  // Save section
  useEffect(() => {
    if (currentSection) {
      localStorage.setItem('currentSection', currentSection.id);
    }
  }, [currentSection]);

  // Save chat history
  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
  }, [chatHistory]);

  const handleSectionSelect = (section) => {
    setCurrentSection(section);
    setPrompt('');
    setResult(null);
    setError(null);
    // Clear current messages when switching sections
  };

  const handleBackToSections = () => {
    setCurrentSection(null);
    setPrompt('');
    setResult(null);
    setError(null);
  };

  // const toggleTheme = () => {
  //   const newTheme = theme === 'dark' ? 'light' : 'dark';
  //   setTheme(newTheme);
  //   setToast(`Switched to ${newTheme} mode`);
  //   setTimeout(() => setToast(null), 2000);
  // };

  const clearChat = () => {
    if (currentSection) {
      setChatHistory(prev => ({
        ...prev,
        [currentSection.id]: []
      }));
    }
    setResult(null);
    setToast('Chat cleared');
    setTimeout(() => setToast(null), 2000);
  };

  const exportAsTXT = () => {
    if (!currentSection) return;
    const sectionHistory = chatHistory[currentSection.id] || [];
    const content = sectionHistory.map(msg => {
      const timestamp = new Date(msg.timestamp).toLocaleString();
      return `[${timestamp}] ${msg.role === 'user' ? 'You' : 'AI'}: ${msg.content}`;
    }).join('\n\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentSection.name.toLowerCase()}-chat-history.txt`;
    a.click();
    URL.revokeObjectURL(url);
    setToast('Exported as TXT');
    setTimeout(() => setToast(null), 2000);
  };

  const exportAsPDF = () => {
    if (!currentSection) return;
    const sectionHistory = chatHistory[currentSection.id] || [];
    const doc = new jsPDF();
    let y = 20;
    doc.setFontSize(16);
    doc.text(`${currentSection.name} Chat History`, 20, y);
    y += 20;

    sectionHistory.forEach(msg => {
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
      const timestamp = new Date(msg.timestamp).toLocaleString();
      doc.setFontSize(10);
      doc.text(`[${timestamp}] ${msg.role === 'user' ? 'You' : 'AI'}:`, 20, y);
      y += 10;
      doc.setFontSize(12);
      const lines = doc.splitTextToSize(msg.content, 170);
      lines.forEach(line => {
        if (y > 270) {
          doc.addPage();
          y = 20;
        }
        doc.text(line, 20, y);
        y += 7;
      });
      y += 10;
    });

    doc.save(`${currentSection.name.toLowerCase()}-chat-history.pdf`);
    setToast('Exported as PDF');
    setTimeout(() => setToast(null), 2000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsLoading(true);
    setIsTyping(true);
    setError(null);
    const currentPrompt = prompt;
    setPrompt('');

    const userMessage = { role: 'user', content: currentPrompt, timestamp: new Date().toISOString() };
    setChatHistory(prev => ({
      ...prev,
      [currentSection.id]: [...(prev[currentSection.id] || []), userMessage]
    }));

    try {
      const res = await fetch('http://localhost:5000/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: currentPrompt, current_section: currentSection.id })
      });

      if (!res.ok) {
        throw new Error('Failed to get response');
      }

      const data = await res.json();

      // Handle auto section switching
      if (data.redirect) {
        const previousSection = currentSection;
        const newSection = sections.find(s => s.id === data.section);
        setCurrentSection(newSection);
        setToast(`Switched from ${previousSection.name} to ${newSection.name} section 🚀`);
        setTimeout(() => setToast(null), 3000);
        // Update chat history for the new section with user message and AI response
        const aiMessage = { role: 'assistant', content: data.response, timestamp: new Date().toISOString() };
        setChatHistory(prev => ({
          ...prev,
          [newSection.id]: [...(prev[newSection.id] || []), userMessage, aiMessage]
        }));
        // Scroll to bottom
        setTimeout(() => {
          const chatContainer = document.querySelector('.max-h-96.overflow-y-auto');
          if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 100);
      } else {
        // Update chat history for the current section with user message and AI response
        const aiMessage = { role: 'assistant', content: data.response, timestamp: new Date().toISOString() };
        setChatHistory(prev => ({
          ...prev,
          [currentSection.id]: [...(prev[currentSection.id] || []), userMessage, aiMessage]
        }));
        // Scroll to bottom
        setTimeout(() => {
          const chatContainer = document.querySelector('.max-h-96.overflow-y-auto');
          if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 100);
      }

      setResult(data);
    } catch (err) {
      setError('Failed to connect to the server. Make sure the backend is running!');
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const tryExample = (examplePrompt) => {
    setPrompt(examplePrompt);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setToast('Copied!');
    setTimeout(() => setToast(null), 2000);
  };

  const TypingAnimation = ({ text }) => {
    const [displayedText, setDisplayedText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
      if (currentIndex < text.length) {
        const timer = setTimeout(() => {
          setDisplayedText(prev => prev + text[currentIndex]);
          setCurrentIndex(prev => prev + 1);
        }, 20);
        return () => clearTimeout(timer);
      }
    }, [currentIndex, text]);

    return <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>{displayedText}</ReactMarkdown>;
  };

  const MessageBubble = ({ message, isLast }) => {
    const isUser = message.role === 'user';
    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
          <div className={`relative p-4 rounded-lg ${
            isUser
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-900'
          }`}>
            {!isUser && (
              <button
                onClick={() => copyToClipboard(message.content)}
                className="absolute top-2 right-2 p-1 rounded hover:bg-gray-300 transition-colors"
                title="Copy to clipboard"
              >
                <Copy size={16} />
              </button>
            )}
            <div className="leading-relaxed">
              {isLast && isTyping ? (
                <TypingAnimation text={message.content} />
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                  {message.content}
                </ReactMarkdown>
              )}
            </div>
          </div>
          <div className={`text-xs mt-1 text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}>
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  if (!currentSection) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <div className="max-w-6xl w-full">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4 text-gray-900">Prompt Companion</h1>
            <p className="text-xl text-gray-600">Choose your AI expert for specialized conversations</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {sections.map((section, index) => (
              <div
                key={section.id}
                className={`${section.color} rounded-lg p-6 cursor-pointer border border-gray-300 hover:border-gray-400 transition-colors`}
                onClick={() => handleSectionSelect(section)}
              >
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-white mb-2">{section.name}</h3>
                  <div className="space-y-1">
                    {section.examples.slice(0, 2).map((example, i) => (
                      <p key={i} className="text-white/80 text-sm">{example}</p>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <div className="max-w-4xl mx-auto p-6">
        {/* Top Bar */}
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={handleBackToSections}
            className="text-gray-600 hover:text-gray-900"
          >
            Back to Sections
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={clearChat}
              className="p-2 rounded hover:bg-gray-200 transition-colors"
              title="Clear chat"
            >
              <Trash2 size={20} />
            </button>
            <button
              onClick={exportAsTXT}
              className="p-2 rounded hover:bg-gray-200 transition-colors"
              title="Export as TXT"
            >
              <Download size={20} />
            </button>
            <button
              onClick={exportAsPDF}
              className="p-2 rounded hover:bg-gray-200 transition-colors"
              title="Export as PDF"
            >
              <Download size={20} />
            </button>
          </div>
        </div>

        <div className="mb-8">
          <div>
            <h1 className="text-3xl font-bold">{currentSection.name} Assistant</h1>
            <p className="text-gray-600">Ask me anything about {currentSection.name.toLowerCase()}!</p>
          </div>
        </div>

        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-3">Try these examples:</h3>
          <div className="flex flex-wrap gap-2">
            {currentSection.examples.map((example, index) => (
              <button
                key={index}
                onClick={() => tryExample(example)}
                className="px-4 py-2 rounded border border-gray-300 hover:bg-gray-100 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="mb-8"
        >
          <div className="flex flex-col gap-4">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={`Ask something about ${currentSection.name}...`}
              className="w-full p-4 rounded border border-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
            />
            <button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed px-8 py-3 rounded font-semibold text-white"
            >
              {isLoading ? 'Thinking...' : 'Ask AI'}
            </button>
          </div>
        </form>

        {/* Chat History */}
        <div className="space-y-4 mb-8 max-h-96 overflow-y-auto">
          {(chatHistory[currentSection.id] || []).map((message, index) => (
            <MessageBubble
              key={index}
              message={message}
              isLast={index === (chatHistory[currentSection.id] || []).length - 1 && isTyping}
            />
          ))}
        </div>

        {error && (
          <div className="border border-red-300 p-4 rounded mb-6 bg-red-100 text-red-800">
            {error}
          </div>
        )}

        {toast && (
          <div className="border border-blue-300 p-4 rounded mb-6 bg-blue-100 text-blue-800">
            {toast}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
