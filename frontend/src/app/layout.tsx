import type { Metadata } from "next";
import { Inter, Hanken_Grotesk } from "next/font/google";
import Navigation from "@/components/Navigation";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const hanken = Hanken_Grotesk({
  variable: "--font-hanken",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ICICI Prudential FAQ Assistant",
  description: "Factual ICICI Prudential Mutual Fund AI Assistant – Facts-only, no investment advice.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${hanken.variable} antialiased bg-bg-page text-text-main h-screen flex flex-col overflow-hidden`}>
        <Navigation />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-hidden bg-bg-page">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
