import type { AttemptPoint } from "@/lib/api/types";

// Single-series line chart (score % across attempts on one paper). Per the
// dataviz method: a lone series needs no legend (the card title already
// says what's plotted), gets one accent hue (not the app's neutral
// `--primary`), and a direct label only at the endpoint. This blue
// (#2a78d6) is validated via the skill's contrast/CVD checker against a
// white surface — see the reports page for context.
const LINE_COLOR = "#2a78d6";
const BASELINE_COLOR = "#e1e0d9";

const WIDTH = 220;
const HEIGHT = 72;
const PAD_X = 8;
const PAD_TOP = 16;
const PAD_BOTTOM = 10;

export function TrendChart({ attempts }: { attempts: AttemptPoint[] }) {
  const points = attempts.map((a, i) => {
    const t = attempts.length > 1 ? i / (attempts.length - 1) : 0;
    const x = PAD_X + t * (WIDTH - PAD_X * 2);
    const pct = a.percent ?? 0;
    const y = HEIGHT - PAD_BOTTOM - (pct / 100) * (HEIGHT - PAD_TOP - PAD_BOTTOM);
    return { x, y, attempt: a };
  });

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const last = points[points.length - 1];
  const first = points[0];

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      width={WIDTH}
      height={HEIGHT}
      role="img"
      aria-label={`Score trend across ${attempts.length} attempts, from ${first.attempt.percent ?? 0}% to ${last.attempt.percent ?? 0}%`}
    >
      <line
        x1={PAD_X}
        y1={HEIGHT - PAD_BOTTOM}
        x2={WIDTH - PAD_X}
        y2={HEIGHT - PAD_BOTTOM}
        stroke={BASELINE_COLOR}
        strokeWidth={1}
      />
      <path
        d={linePath}
        fill="none"
        stroke={LINE_COLOR}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {points.map((p) => (
        <circle
          key={p.attempt.attempt_id}
          cx={p.x}
          cy={p.y}
          r={4}
          fill={LINE_COLOR}
          stroke="#ffffff"
          strokeWidth={2}
        >
          <title>
            Attempt {p.attempt.attempt_number}: {p.attempt.percent ?? 0}%
            {p.attempt.score !== null && p.attempt.max_score !== null
              ? ` (${p.attempt.score}/${p.attempt.max_score} pts)`
              : ""}
          </title>
        </circle>
      ))}
      <text
        x={last.x}
        y={Math.max(10, last.y - 8)}
        textAnchor="middle"
        fontSize={11}
        className="fill-foreground font-medium"
      >
        {last.attempt.percent ?? 0}%
      </text>
    </svg>
  );
}
