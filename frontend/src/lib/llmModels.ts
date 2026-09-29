// Curated model catalogs shown as dropdown options in Admin → LLM Settings.
// Each provider row still stores a plain model_name string — picking from
// here just fills that field. "Custom model ID…" always falls back to free
// text, so an outdated/missing entry here never blocks configuring a model.

export interface ModelOption {
  id: string;
  label: string;
  price?: string;
  description: string;
}

export const ANTHROPIC_MODELS: ModelOption[] = [
  {
    id: "claude-opus-5-5",
    label: "Claude Opus 5.5",
    price: "$4.00 / $20.00",
    description: "Complex reasoning and agentic workflows",
  },
  {
    id: "claude-fable-5-1",
    label: "Claude Fable 5.1",
    price: "$10.00 / $50.00",
    description: "Scientific discovery and autonomous operations",
  },
  {
    id: "claude-sonnet-5",
    label: "Claude Sonnet 4.6",
    price: "$3.00 / $15.00",
    description: "Balanced general performance and speed",
  },
  {
    id: "claude-haiku-4-5-20251001",
    label: "Claude Haiku 4.5",
    price: "$1.00 / $5.00",
    description: "Ultra-fast routing and high-volume tasks",
  },
];

// No official pricing was supplied for these — figures were left off
// rather than guessed. Update this list (and add `price` strings) once
// you've got exact numbers you want shown.
export const OPENAI_MODELS: ModelOption[] = [
  {
    id: "gpt-5",
    label: "GPT-5",
    description: "Flagship reasoning and agentic workflows",
  },
  {
    id: "gpt-5-mini",
    label: "GPT-5 Mini",
    description: "Balanced general performance and speed",
  },
  {
    id: "gpt-5-nano",
    label: "GPT-5 Nano",
    description: "Ultra-fast routing and high-volume tasks",
  },
  {
    id: "gpt-4.1",
    label: "GPT-4.1",
    description: "Previous-generation flagship, still widely supported",
  },
  {
    id: "gpt-4o-mini",
    label: "GPT-4o Mini",
    description: "Low-cost legacy option",
  },
];
