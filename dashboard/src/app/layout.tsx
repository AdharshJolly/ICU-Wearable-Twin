import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Activity, LayoutDashboard, Settings } from "lucide-react";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ICU Wearable Twin",
  description: "High-Fidelity AI Patient Digital Twin",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="h-full flex flex-col md:flex-row bg-[#020617] text-slate-50 overflow-hidden">
        {/* Responsive Navigation: Bottom on mobile, Side on desktop */}
        <aside className="w-full h-16 md:w-16 lg:w-20 md:h-full border-t md:border-t-0 md:border-r border-slate-800/60 bg-slate-950/80 backdrop-blur-xl flex flex-row md:flex-col items-center justify-around md:justify-start py-0 md:py-6 flex-shrink-0 z-50 order-last md:order-first">
          <div className="hidden md:flex w-10 h-10 rounded-xl bg-blue-500/20 items-center justify-center border border-blue-500/30 mb-8 shadow-lg shadow-blue-500/10">
            <Activity className="text-blue-400 w-5 h-5" />
          </div>
          
          <nav className="flex flex-row md:flex-col items-center justify-center md:justify-start gap-2 md:gap-6 w-full md:flex-1 h-full md:h-auto px-4 md:px-0">
            <Link href="/" aria-label="Ward View" className="p-3 rounded-xl bg-slate-800/50 text-slate-200 border border-slate-700/50 transition-colors tooltip-trigger relative group">
              <LayoutDashboard className="w-5 h-5" />
              <span className="hidden md:block absolute left-14 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700 pointer-events-none">Ward View</span>
            </Link>
          </nav>

          <div className="hidden md:flex mt-auto flex-col gap-4">
            <button aria-label="Settings" className="p-3 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-slate-800/30 transition-colors group relative">
              <Settings className="w-5 h-5" />
              <span className="hidden md:block absolute left-14 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700 pointer-events-none text-slate-200">Settings</span>
            </button>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 h-[calc(100%-4rem)] md:h-full overflow-y-auto relative bg-[#020617] order-first md:order-last">
          {children}
        </main>
      </body>
    </html>
  );
}
