"use client";

import { X, Send } from "lucide-react";
import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  query: string;
  platform: string;
  start: string;
  end: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  suggestions?: string[];
  isError?: boolean;
}

export default function ChatPanel({ isOpen, onClose, query, platform, start, end }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      role: "assistant",
      content: "Hello! I'm the NarrativeTrace Assistant. Ask me anything about the data you're exploring.",
      suggestions: [
        "Which subreddits are most active?",
        "Who are the top contributors?",
        "What topics are trending this week?",
      ],
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  
  const endRef = useRef<HTMLDivElement>(null);

  // Auto scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    
    // Optimistic UI update
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // Prepare history payload format
    const historyPayload = messages.map(m => ({
      role: m.role,
      content: m.content
    }));

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: historyPayload,
          context: `Query: "${query}", Date range: ${start} to ${end}, Platform: ${platform}, Dataset: Reddit Feb 2025`
        }),
      });
      
      const data = await res.json();
      
      if (!res.ok || data.error) {
        const errMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data?.error || "Sorry, the assistant is unavailable. The AI may be rate-limited — try again in a minute.",
          isError: true
        };
        setMessages(prev => [...prev, errMsg]);
        return;
      }

      const astMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer || "No response provided.",
        suggestions: data.suggestions || [],
      };
      setMessages(prev => [...prev, astMsg]);
      
    } catch (err: any) {
      console.log("Chat fetch issue:", err?.message || "Failed");
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, the assistant is unavailable. The AI may be rate-limited \u2014 try again in a minute.",
        isError: true
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const onFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  return (
    <>
      {/* Backdrop for mobile closing optionally, or just letting it slide freely */}
      <div 
        className={`fixed inset-0 bg-black/5 z-40 transition-opacity duration-300 ${isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
        onClick={onClose}
      />
      
      <div 
        className={`fixed inset-y-0 right-0 w-full sm:w-96 bg-white border-l shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ease-in-out ${isOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between p-4 border-b bg-gray-50/80 backdrop-blur-sm">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-blue-600 text-xl font-black">✦</span> NarrativeTrace Assistant
          </h2>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-gray-200 rounded-full text-gray-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Message List ── */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-5 bg-white">
          {messages.map((m) => (
            <div key={m.id} className="flex flex-col gap-3">
              <div className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div 
                  className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-[15px] leading-relaxed shadow-sm overflow-hidden ${
                    m.role === "user" 
                      ? "bg-blue-600 text-white rounded-br-sm" 
                      : m.isError 
                        ? "bg-red-50 text-red-600 border border-red-100 rounded-bl-sm"
                        : "bg-gray-100 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  {m.role === "assistant" && !m.isError ? (
                    <div className="prose prose-sm max-w-none text-gray-800">
                      <ReactMarkdown 
                        components={{
                          p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                          strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                          ul: ({children}) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                          li: ({children}) => <li className="text-gray-700">{children}</li>,
                        }}
                      >
                        {m.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <span className="whitespace-pre-wrap">{m.content}</span>
                  )}
                </div>
              </div>
              
              {/* Render Suggestion Chips if they exist directly underneath the assistant bubble */}
              {m.role === "assistant" && m.suggestions && m.suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2 pl-2">
                  {m.suggestions.map((sug, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(sug)}
                      disabled={loading}
                      className="text-xs bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full hover:bg-gray-50 hover:text-gray-900 transition-colors shadow-sm disabled:opacity-50 text-left"
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-1.5">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
              </div>
            </div>
          )}
          <div ref={endRef} className="h-px" />
        </div>

        {/* ── Input Box ── */}
        <div className="p-4 border-t bg-white">
          <form onSubmit={onFormSubmit} className="relative flex items-center">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..." 
              disabled={loading}
              className="w-full bg-gray-50 border border-gray-200 rounded-full pl-4 pr-12 py-3 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 text-gray-900 transition-all text-[15px] shadow-sm disabled:opacity-60"
            />
            <button 
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 text-white rounded-full transition-colors flex items-center justify-center pointer-events-auto"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
