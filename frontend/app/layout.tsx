import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import "./globals.css";

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-poppins",
});

export const metadata: Metadata = {
  title: "NarrativeTrace — Social Media Narrative Analysis",
  description:
    "Search any topic to see who's talking about it, how activity changes over time, and which communities are most active.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${poppins.variable} h-full antialiased`}>
      <body
        className="min-h-full flex flex-col bg-gray-50"
        style={{ fontFamily: "var(--font-poppins), system-ui, sans-serif" }}
      >
        {children}
      </body>
    </html>
  );
}
