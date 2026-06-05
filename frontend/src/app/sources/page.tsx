"use client";

import { useState, useEffect } from 'react';

type Source = {
  url: string;
  source_type: string;
  scheme: string;
  title: string;
  fetched_date: string;
};

// Map scheme IDs to display categories
const CATEGORY_MAP: Record<string, string> = {
  retirement_pure_equity: "RETIREMENT",
  retirement_hybrid: "RETIREMENT",
  pharma: "SECTORAL",
  bharat22: "FOF",
  infrastructure: "SECTORAL",
  select_large_cap: "LARGE-CAP",
  india_equity: "FOF",
  top100: "LARGE-CAP",
  diversified_equity: "FLEXI-CAP",
  value: "VALUE",
  dynamic: "DYNAMIC",
  balanced: "HYBRID",
  large_cap: "LARGE-CAP",
  consumption: "THEMATIC",
  income_plus_arbitrage: "FOF",
  technology: "SECTORAL",
  india_opportunities: "THEMATIC",
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/sources`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch");
        return res.json();
      })
      .then(data => {
        setSources(data);
        setIsLoading(false);
      })
      .catch(() => {
        setError("Could not load sources. Is the FastAPI backend running?");
        setIsLoading(false);
      });
  }, []);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-[1100px] mx-auto px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-text-main mb-3">The Source Hub</h1>
          <p className="font-body text-base text-text-secondary max-w-2xl">
            A verified repository of core ICICI Prudential Mutual Fund schemes, regulatory documents, and investor education resources. All information is direct from official filings.
          </p>
        </div>

        {error ? (
          <div className="p-5 rounded-xl bg-[#ffdad6] text-[#ba1a1a] font-semibold text-sm border border-[#ba1a1a]/20">
            {error}
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-20 text-text-helper">Loading sources...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {sources.map((src, i) => {
              const category = CATEGORY_MAP[src.scheme] || "EQUITY";
              return (
                <div
                  key={i}
                  className="group flex flex-col p-6 bg-bg-surface border border-gray-border rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.6)] transition-all relative overflow-hidden"
                >
                  {/* Decorative background icon */}
                  <div className="absolute top-4 right-4 opacity-[0.06]">
                    <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                  </div>

                  {/* Category chip */}
                  <span className="inline-block w-fit px-3 py-1 bg-brand-green-light text-[#00533c] text-[11px] font-bold font-heading rounded-full mb-4 uppercase tracking-wider">
                    {category}
                  </span>

                  {/* Title */}
                  <h3 className="font-heading text-lg font-bold text-text-main leading-snug mb-6 flex-1">
                    {src.title}
                  </h3>

                  {/* Links */}
                  <div className="pt-4 border-t border-gray-border flex flex-col gap-2">
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between text-brand-green font-semibold text-sm hover:text-brand-green-hover transition-colors group/link"
                    >
                      Official Scheme Page
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover/link:translate-x-0.5 transition-transform">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                      </svg>
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Investor Resources section */}
        <div className="mt-12 p-8 bg-bg-surface border border-gray-border rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
          <h2 className="font-heading text-xl font-bold text-text-main mb-2">Investor Resources</h2>
          <p className="font-body text-sm text-text-secondary max-w-lg">
            Access general regulatory guidelines and educational content to make informed investment decisions.
          </p>
          <div className="flex gap-3 mt-4">
            <a href="https://www.amfiindia.com" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-brand-green-light text-brand-green text-xs font-bold rounded-lg hover:bg-[#c2f3e5] transition-colors">
              AMFI India
            </a>
            <a href="https://www.sebi.gov.in" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-brand-green-light text-brand-green text-xs font-bold rounded-lg hover:bg-[#c2f3e5] transition-colors">
              SEBI
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
