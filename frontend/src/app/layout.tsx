import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { RoleProvider } from "@/context/RoleContext";
import { MainNav } from "@/components/nav/MainNav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Scioly Prep",
  description:
    "Science Olympiad practice-exam tool for home tutoring students.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <RoleProvider>
          <MainNav />
          <main className="flex-1">{children}</main>
        </RoleProvider>
      </body>
    </html>
  );
}
