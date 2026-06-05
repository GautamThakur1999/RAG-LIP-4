"use client";

import Link from 'next/link';

const FAQ_CARDS = [
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
      </svg>
    ),
    question: "What is the exit load for ICICI Prudential Technology Fund?",
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
        <line x1="16" y1="2" x2="16" y2="6"></line>
        <line x1="8" y1="2" x2="8" y2="6"></line>
        <line x1="3" y1="10" x2="21" y2="10"></line>
      </svg>
    ),
    question: "Minimum SIP for ICICI Prudential Value Fund?",
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
      </svg>
    ),
    question: "Who is the fund manager for the Infrastructure fund?",
  },
];

const SUGGESTION_CHIPS = ["Equity Funds", "Debt Taxation", "Redemption Process"];

export default function HomePage() {
  return (
    <div className="h-full overflow-y-auto flex flex-col">
      {/* Main content */}
      <div className="flex-1 flex flex-col items-center px-8 pt-12 pb-8 max-w-[900px] mx-auto w-full">
        {/* Icon */}
        <div className="w-16 h-16 rounded-2xl bg-brand-green flex items-center justify-center mb-8 shadow-[0_4px_20px_rgba(0,208,156,0.3)]">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
          </svg>
        </div>

        {/* Title */}
        <h1 className="font-heading text-4xl md:text-[42px] font-bold text-text-main text-center leading-tight mb-5">
          Welcome to the ICICI Prudential FAQ Assistant
        </h1>

        {/* Disclaimer badge */}
        <div className="inline-flex items-center px-5 py-2.5 bg-brand-green-light border border-[#a8e6cf] rounded-full mb-6">
          <span className="text-[#00533c] text-sm font-bold font-heading tracking-widest uppercase">
            Facts-Only. No Investment Advice.
          </span>
        </div>

        {/* Subtitle */}
        <p className="text-text-secondary font-body text-lg text-center max-w-[640px] mb-10">
          Your intelligent companion for exploring ICICI Prudential Mutual Fund schemes, policies, and documents with absolute clarity.
        </p>

        {/* FAQ Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 w-full mb-10">
          {FAQ_CARDS.map((card, i) => (
            <Link
              key={i}
              href={`/chat?q=${encodeURIComponent(card.question)}`}
              className="group flex flex-col p-6 bg-bg-surface border border-gray-border rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.6)] transition-all"
            >
              <div className="mb-4">{card.icon}</div>
              <p className="font-heading text-base font-semibold text-text-main leading-snug flex-1">
                {card.question}
              </p>
              <div className="mt-4 flex items-center gap-1 text-brand-green text-sm font-semibold group-hover:gap-2 transition-all">
                Ask now
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </div>
            </Link>
          ))}
        </div>

        {/* Trusted Intelligence Banner */}
        <div className="w-full rounded-2xl bg-gradient-to-r from-[#006c4f] to-[#00D09C] p-8 text-white">
          <h3 className="font-heading text-2xl font-bold mb-2">Trusted Intelligence</h3>
          <p className="font-body text-sm opacity-90 max-w-lg">
            Every answer is grounded in official scheme documents. No speculation, no opinions — just verified financial facts sourced directly from ICICI Prudential filings.
          </p>
        </div>
      </div>

      {/* Bottom Input Area */}
      <div className="sticky bottom-0 bg-bg-page border-t border-gray-border px-8 py-4">
        <div className="max-w-[900px] mx-auto w-full">
          <form
            onSubmit={(e) => { e.preventDefault(); }}
            className="flex items-center gap-3"
          >
            <div className="relative flex-1 flex items-center bg-bg-chat border border-gray-border rounded-xl transition-colors focus-within:border-brand-green focus-within:ring-1 focus-within:ring-brand-green">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7C7E8C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-4">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <input
                type="text"
                placeholder="Ask about funds, exit loads, or policies..."
                className="w-full py-3.5 pl-3 pr-4 bg-transparent outline-none text-text-main placeholder:text-text-helper font-body text-sm"
              />
            </div>
            <Link
              href="/chat"
              className="flex items-center gap-2 py-3.5 px-6 bg-brand-green text-white text-sm font-bold rounded-xl hover:bg-brand-green-hover transition-colors"
            >
              Send
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </Link>
          </form>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-text-helper font-medium">Suggestions:</span>
            {SUGGESTION_CHIPS.map((chip) => (
              <Link
                key={chip}
                href={`/chat?q=${encodeURIComponent(chip)}`}
                className="px-3 py-1 bg-brand-green-light text-brand-green text-xs font-semibold rounded-full hover:bg-[#c2f3e5] transition-colors"
              >
                {chip}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
