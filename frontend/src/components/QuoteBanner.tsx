"use client";

import { useEffect, useState } from "react";
import { Quote } from "lucide-react";

export const QUOTES = [
  {
    text: "The important thing is not to stop questioning.",
    author: "Albert Einstein",
  },
  {
    text: "Somewhere, something incredible is waiting to be known.",
    author: "Carl Sagan",
  },
  {
    text: "Science is a way of thinking much more than it is a body of knowledge.",
    author: "Carl Sagan",
  },
  {
    text: "What we know is a drop, what we don't know is an ocean.",
    author: "Isaac Newton",
  },
  {
    text: "Nothing in life is to be feared, it is only to be understood.",
    author: "Marie Curie",
  },
  {
    text: "I have not failed. I've just found 10,000 ways that won't work.",
    author: "Thomas Edison",
  },
  {
    text: "Genius is one percent inspiration and ninety-nine percent perspiration.",
    author: "Thomas Edison",
  },
  {
    text: "An investment in knowledge pays the best interest.",
    author: "Benjamin Franklin",
  },
  {
    text: "Education is the most powerful weapon which you can use to change the world.",
    author: "Nelson Mandela",
  },
  {
    text: "It always seems impossible until it's done.",
    author: "Nelson Mandela",
  },
  {
    text: "The beautiful thing about learning is that no one can take it away from you.",
    author: "B.B. King",
  },
  {
    text: "Curiosity is the wick in the candle of learning.",
    author: "William Arthur Ward",
  },
  {
    text: "The expert in anything was once a beginner.",
    author: "Helen Hayes",
  },
  {
    text: "The secret of getting ahead is getting started.",
    author: "Mark Twain",
  },
  {
    text: "You don't have to be great to start, but you have to start to be great.",
    author: "Zig Ziglar",
  },
  {
    text: "Success is the sum of small efforts, repeated day in and day out.",
    author: "Robert Collier",
  },
  {
    text: "The only way to do great work is to love what you do.",
    author: "Steve Jobs",
  },
  {
    text: "The future belongs to those who believe in the beauty of their dreams.",
    author: "Eleanor Roosevelt",
  },
  {
    text: "Strive for progress, not perfection.",
    author: "Unknown",
  },
  {
    text: "The more I learn, the more I realize how much I don't know.",
    author: "Albert Einstein",
  },
] as const;

export function QuoteBanner() {
  const [quote, setQuote] = useState<(typeof QUOTES)[number] | null>(null);

  useEffect(() => {
    setQuote(QUOTES[Math.floor(Math.random() * QUOTES.length)]);
  }, []);

  return (
    <aside
      aria-label="Inspirational quote"
      className="w-full border-b bg-primary text-primary-foreground"
    >
      <div className="mx-auto flex min-h-16 max-w-6xl items-center gap-3 px-4 py-3 sm:gap-4 sm:px-6">
        <Quote
          className="size-5 shrink-0 opacity-80"
          aria-hidden="true"
        />
        <p
          className={`text-sm leading-relaxed sm:text-base ${quote ? "opacity-100" : "opacity-0"}`}
        >
          {quote ? (
            <>
              <span className="italic">&ldquo;{quote.text}&rdquo;</span>
              <span className="ml-2 font-medium not-italic opacity-80">
                — {quote.author}
              </span>
            </>
          ) : (
            <span>&nbsp;</span>
          )}
        </p>
      </div>
    </aside>
  );
}
