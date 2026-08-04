import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "SevenFive Service - Commercial Equipment & Spare Parts Catalog",
  description: "Official SevenFive spare parts catalog, exploded assembly diagrams, machine model specs, and technical support documentation.",
  keywords: "SevenFive, Sirman, spare parts, commercial kitchen equipment, exploded view, slicers, food processors, meat grinders",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#F8FAFC] text-slate-900 font-sans selection:bg-[#C8102E] selection:text-white">
        {children}
      </body>
    </html>
  );
}
