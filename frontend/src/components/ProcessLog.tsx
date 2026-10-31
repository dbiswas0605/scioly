"use client";

import { useEffect, useRef } from "react";

export type ProcessLogEntry = {
  timestamp: string;
  message: string;
};

export function createProcessLogEntry(message: string): ProcessLogEntry {
  return {
    timestamp: new Date().toLocaleTimeString(),
    message,
  };
}

export function ProcessLog({
  entries,
  running,
}: {
  entries: ProcessLogEntry[];
  running: boolean;
}) {
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [entries]);

  return (
    <section
      aria-label="Document processing log"
      className="overflow-hidden rounded-lg border border-emerald-500/30 bg-black shadow-inner"
    >
      <div className="flex items-center justify-between border-b border-emerald-900/80 bg-zinc-950 px-3 py-2 font-mono text-[11px] uppercase tracking-wider text-emerald-400">
        <span>Process log</span>
        <span>{running ? "Running" : "Latest run"}</span>
      </div>
      <div
        ref={logRef}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        className="h-36 overflow-y-auto px-3 py-2 font-mono text-xs leading-5 text-green-400"
      >
        {entries.map((entry, index) => (
          <p key={`${entry.timestamp}-${index}`} className="break-words">
            <span className="mr-2 text-emerald-500">[{entry.timestamp}]</span>
            <span className="mr-1 text-green-500">&gt;</span>
            {entry.message}
          </p>
        ))}
        {running ? (
          <p className="animate-pulse text-emerald-500" aria-hidden="true">
            _
          </p>
        ) : null}
      </div>
    </section>
  );
}
