import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Activity, LayoutDashboard, Users, Settings, Database, BrainCircuit } from "lucide-react";
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
      <body className="h-full flex bg-[#020617] text-slate-50 overflow-hidden">
        {/* Persistent Side Navigation */}
        <aside className="w-16 lg:w-20 border-r border-slate-800/60 bg-slate-950/80 backdrop-blur-xl flex flex-col items-center py-6 flex-shrink-0 z-50">
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center border border-blue-500/30 mb-8 shadow-lg shadow-blue-500/10">
            <Activity className="text-blue-400 w-5 h-5" />
          </div>
          
          <nav className="flex-1 flex flex-col items-center gap-6 w-full">
            <a href="/" className="p-3 rounded-xl bg-slate-800/50 text-slate-200 border border-slate-700/50 transition-colors tooltip-trigger relative group">
              <LayoutDashboard className="w-5 h-5" />
              <span className="absolute left-14 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700">Ward View</span>
            </a>
            <button className="p-3 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-slate-800/30 transition-colors group relative">
              <Users className="w-5 h-5" />
              <span className="absolute left-14 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700 text-slate-200">Patient Roster</span>
            </button>
            <button className="p-3 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-slate-800/30 transition-colors group relative">
              <BrainCircuit className="w-5 h-5" />
              <span className="absolute left-14 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700 text-slate-200">Digital Twins</span>
            </button>
            <button className="p-3 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-slate-800/30 transition-colors group relative">
              <Database className="w-5 h-5" />
              <span className="absolute left-14 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700 text-slate-200">Data Logs</span>
            </button>
          </nav>

          <div className="mt-auto flex flex-col gap-4">
            <button className="p-3 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-slate-800/30 transition-colors">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 h-full overflow-y-auto relative bg-[#020617]">
          {children}
        </main>
      </body>
    </html>
  );
}
