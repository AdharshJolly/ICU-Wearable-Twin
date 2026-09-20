import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
      <body className="h-full bg-[#020617] text-slate-50 overflow-hidden">
        {/* Main Content Area - Full Bleed */}
        <main className="w-full h-full overflow-y-auto relative">
          {children}
        </main>
      </body>
    </html>
  );
}
