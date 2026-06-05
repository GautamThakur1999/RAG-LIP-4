"use client";

import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  citation?: string;
  last_updated?: string;
  kind?: string;
};

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q');
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const hasAutoSent = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text }),
      });

      if (!response.ok) {
        throw new Error('API Error');
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        citation: data.citation,
        lastUpdated: data.last_updated,
        kind: data.kind
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I couldn't connect to the FAQ API. Please try again later."
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (initialQuery && !hasAutoSent.current) {
      hasAutoSent.current = true;
      handleSend(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  return (
    <div className="h-full flex flex-col">
      {/* Facts-only banner */}
      <div className="flex items-center justify-center gap-2 py-2 bg-bg-surface border-b border-gray-border text-sm text-text-secondary font-medium shrink-0">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        FACTS-ONLY. NO INVESTMENT ADVICE.
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-[800px] mx-auto flex flex-col gap-6">
          {messages.length === 0 && !isLoading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-20">
              <div className="w-14 h-14 rounded-2xl bg-brand-green-light flex items-center justify-center mb-6">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <h2 className="font-heading text-2xl font-bold text-text-main mb-2">Start a conversation</h2>
              <p className="text-text-helper text-sm max-w-md">Ask any factual question about ICICI Prudential mutual funds and I&apos;ll provide verified answers.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-brand-green flex items-center justify-center shrink-0 mr-3 mt-1">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                  </svg>
                </div>
              )}
              <div className={`max-w-[75%] rounded-2xl p-5 ${
                msg.role === 'user'
                  ? 'bg-brand-green text-white rounded-tr-sm'
                  : 'bg-bg-surface border border-gray-border text-text-main rounded-tl-sm shadow-[0_4px_20px_rgba(0,0,0,0.4)]'
              }`}>
                <div className="font-body text-[15px] leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                </div>

                {msg.role === 'assistant' && msg.citation && (
                  <div className="mt-4 pt-3 border-t border-gray-border flex flex-col gap-1.5 text-xs text-text-helper">
                    <a href={msg.citation} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-brand-green transition-colors font-semibold">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                      </svg>
                      Source: {msg.citation.split('/').pop()?.replace(/-/g, ' ')}
                    </a>
                    {msg.last_updated && (
                      <span className="flex items-center gap-1.5">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        Last updated from sources: {msg.last_updated}
                      </span>
                    )}
                  </div>
                )}

                {msg.role === 'assistant' && msg.kind === 'refusal' && (
                  <div className="mt-3 inline-flex items-center gap-1.5 text-xs text-[#934b07] bg-[#ffdcc6] px-2.5 py-1 rounded-full font-semibold">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    </svg>
                    Guardrail Activated
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-brand-green flex items-center justify-center shrink-0 mr-3 mt-1">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
              </div>
              <div className="bg-bg-surface border border-gray-border rounded-2xl rounded-tl-sm p-5 shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
                <div className="flex gap-1.5 items-center h-5">
                  <div className="w-2 h-2 bg-brand-green rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-brand-green rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-brand-green rounded-full animate-bounce"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="bg-bg-surface border-t border-gray-border px-8 py-4 shrink-0">
        <div className="max-w-[800px] mx-auto">
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(input); }}
            className="flex items-center gap-3"
          >
            <div className="relative flex-1 flex items-center bg-bg-chat border border-gray-border rounded-xl transition-colors focus-within:border-brand-green focus-within:ring-1 focus-within:ring-brand-green">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about fund details, NAV, or SIPs..."
                className="w-full py-3.5 pl-5 pr-4 bg-transparent outline-none text-text-main placeholder:text-text-helper font-body text-sm"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-3.5 bg-brand-green text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:bg-brand-green-hover transition-colors"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
          <p className="text-center text-xs text-text-helper mt-2 italic">
            AI-generated response based on official fund documents.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-full text-text-helper">Loading chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}
