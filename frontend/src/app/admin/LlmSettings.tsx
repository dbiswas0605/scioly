"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, CircleX, Loader2, PlugZap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { getErrorMessage } from "@/lib/api/client";
import { testLlmProvider, updateLlmProvider } from "@/lib/api/admin";
import { ANTHROPIC_MODELS, OPENAI_MODELS, type ModelOption } from "@/lib/llmModels";
import type { LlmProvider, LlmProviderTestResult } from "@/lib/api/types";

const CUSTOM_MODEL_VALUE = "__custom__";

export function LlmSettings({ providers: initialProviders }: { providers: LlmProvider[] }) {
  const [providers, setProviders] = useState(initialProviders);

  function handleSaved(updated: LlmProvider) {
    setProviders((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  }

  const anthropic = providers.find((p) => p.provider_key === "anthropic");
  const openai = providers.find((p) => p.provider_key === "openai");
  const ollama = providers.find((p) => p.provider_key === "ollama");
  const lmStudio = providers.find((p) => p.provider_key === "lm_studio");
  const mlx = providers.find((p) => p.provider_key === "mlx");

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted-foreground">
        Enabled providers are tried in priority order (lowest number first)
        when parsing an upload, falling back to the next one if a provider
        fails.
      </p>

      {anthropic ? (
        <div className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold">Anthropic</h3>
          <ProviderRow provider={anthropic} modelOptions={ANTHROPIC_MODELS} onSaved={handleSaved} />
        </div>
      ) : null}

      <Separator />

      {openai ? (
        <div className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold">OpenAI</h3>
          <ProviderRow provider={openai} modelOptions={OPENAI_MODELS} onSaved={handleSaved} />
        </div>
      ) : null}

      <Separator />

      <div className="flex flex-col gap-3">
        <div>
          <h3 className="text-sm font-semibold">Local LLM</h3>
          <p className="text-xs text-muted-foreground">
            Point these at a local OpenAI-compatible server — Ollama&apos;s
            built-in <code>/v1</code> endpoint, LM Studio&apos;s local server,
            or MLX via a bridge like <code>mlx_lm.server</code>. Model names
            are whatever you&apos;ve pulled/loaded locally, so there&apos;s no
            fixed dropdown for these.
          </p>
        </div>
        {ollama ? <ProviderRow provider={ollama} onSaved={handleSaved} /> : null}
        {lmStudio ? (
          <div className="flex flex-col gap-3">
            <h4 className="text-sm font-medium">LM Studio</h4>
            <p className="text-xs text-muted-foreground">
              Open the LM Studio desktop at{" "}
              <a
                className="text-primary underline underline-offset-4"
                href="https://localhost:3001"
                target="_blank"
                rel="noreferrer"
              >
                https://localhost:3001
              </a>
              , load a model, and start its local server with network access.
              The default server URL is <code>http://lm-studio:1234/v1</code>.
            </p>
            <ProviderRow provider={lmStudio} onSaved={handleSaved} />
          </div>
        ) : null}
        {mlx ? <ProviderRow provider={mlx} onSaved={handleSaved} /> : null}
      </div>
    </div>
  );
}

function ProviderRow({
  provider,
  modelOptions,
  onSaved,
}: {
  provider: LlmProvider;
  modelOptions?: ModelOption[];
  onSaved: (updated: LlmProvider) => void;
}) {
  const isLocal =
    provider.provider_key === "ollama" ||
    provider.provider_key === "lm_studio" ||
    provider.provider_key === "mlx";

  const [modelName, setModelName] = useState(provider.model_name);
  const [useCustomModel, setUseCustomModel] = useState(
    Boolean(modelOptions) && !modelOptions?.some((m) => m.id === provider.model_name),
  );
  const [baseUrl, setBaseUrl] = useState(provider.base_url ?? "");
  const [apiKey, setApiKey] = useState("");
  const [priority, setPriority] = useState(String(provider.priority));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<LlmProviderTestResult | null>(null);
  const [connectionState, setConnectionState] = useState<
    "checking" | "connected" | "disconnected"
  >("checking");
  const [connectionMessage, setConnectionMessage] = useState("Checking connection…");
  const localDefaultBaseUrl =
    provider.provider_key === "lm_studio"
      ? "http://lm-studio:1234/v1"
      : provider.provider_key === "mlx"
        ? "http://localhost:8080/v1"
        : "http://localhost:11434/v1";

  useEffect(() => {
    if (provider.provider_key !== "lm_studio") return;

    let cancelled = false;
    async function refreshConnectionStatus() {
      try {
        const result = await testLlmProvider(provider.id);
        if (cancelled) return;
        setConnectionState(result.ok ? "connected" : "disconnected");
        setConnectionMessage(result.message);
      } catch (err) {
        if (cancelled) return;
        setConnectionState("disconnected");
        setConnectionMessage(getErrorMessage(err, "Could not check the connection."));
      }
    }

    void refreshConnectionStatus();
    const intervalId = window.setInterval(() => {
      void refreshConnectionStatus();
    }, 30_000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [provider.id, provider.model_name, provider.base_url, provider.provider_key]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    setTestResult(null);
    try {
      const updated = await updateLlmProvider(provider.id, {
        model_name: modelName,
        base_url: baseUrl.trim() ? baseUrl.trim() : null,
        priority: Number(priority) || 0,
        ...(apiKey ? { api_key: apiKey } : {}),
      });
      setApiKey("");
      onSaved(updated);
    } catch (err) {
      setError(getErrorMessage(err, "Could not save changes."));
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleEnabled(checked: boolean) {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateLlmProvider(provider.id, { is_enabled: checked });
      onSaved(updated);
    } catch (err) {
      setError(getErrorMessage(err, "Could not update."));
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setError(null);
    setTestResult(null);
    try {
      const result = await testLlmProvider(provider.id);
      setTestResult(result);
      if (provider.provider_key === "lm_studio") {
        setConnectionState(result.ok ? "connected" : "disconnected");
        setConnectionMessage(result.message);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Could not reach the server."));
    } finally {
      setTesting(false);
    }
  }

  const canTest = isLocal || provider.has_api_key;

  return (
    <div className="flex flex-col gap-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{provider.display_name}</span>
          {isLocal ? <Badge variant="outline">Local</Badge> : null}
          {provider.has_api_key ? (
            <Badge variant="outline">Key configured</Badge>
          ) : !isLocal ? (
            <Badge variant="secondary">No key set</Badge>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            id={`${provider.id}-enabled`}
            checked={provider.is_enabled}
            onCheckedChange={(checked) => handleToggleEnabled(checked === true)}
            disabled={saving}
          />
          <Label htmlFor={`${provider.id}-enabled`} className="text-xs text-muted-foreground">
            Enabled
          </Label>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {modelOptions ? (
          <div className="grid gap-1.5 sm:col-span-2">
            <Label htmlFor={`${provider.id}-model`}>Model</Label>
            <Select
              value={useCustomModel ? CUSTOM_MODEL_VALUE : modelName}
              onValueChange={(value) => {
                if (!value) return;
                if (value === CUSTOM_MODEL_VALUE) {
                  setUseCustomModel(true);
                  return;
                }
                setUseCustomModel(false);
                setModelName(value);
              }}
              disabled={saving}
            >
              <SelectTrigger id={`${provider.id}-model`} className="w-full">
                <SelectValue>
                  {(value: string | null) => {
                    if (value === CUSTOM_MODEL_VALUE) return "Custom model ID…";
                    const option = modelOptions.find((m) => m.id === value);
                    if (!option) return "Choose a model";
                    return `${option.label}${option.price ? ` — ${option.price}` : ""} — ${option.description}`;
                  }}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {modelOptions.map((option) => (
                  <SelectItem key={option.id} value={option.id}>
                    {option.label}
                    {option.price ? ` — ${option.price}` : ""} — {option.description}
                  </SelectItem>
                ))}
                <SelectItem value={CUSTOM_MODEL_VALUE}>Custom model ID…</SelectItem>
              </SelectContent>
            </Select>
            {useCustomModel ? (
              <Input
                value={modelName}
                onChange={(event) => setModelName(event.target.value)}
                placeholder="Exact model ID"
                disabled={saving}
              />
            ) : null}
          </div>
        ) : (
          <div className="grid gap-1.5">
            <Label htmlFor={`${provider.id}-model`}>Model name</Label>
            <Input
              id={`${provider.id}-model`}
              value={modelName}
              onChange={(event) => setModelName(event.target.value)}
              disabled={saving}
            />
          </div>
        )}
        <div className="grid gap-1.5">
          <Label htmlFor={`${provider.id}-priority`}>Priority (lower = tried first)</Label>
          <Input
            id={`${provider.id}-priority`}
            type="number"
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
            disabled={saving}
            className="w-28"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={`${provider.id}-base-url`}>
            {isLocal ? "Server URL" : "Base URL (optional)"}
          </Label>
          <Input
            id={`${provider.id}-base-url`}
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            placeholder={isLocal ? localDefaultBaseUrl : "Default"}
            disabled={saving}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={`${provider.id}-key`}>
            API key{isLocal ? " (optional)" : ""}
          </Label>
          <Input
            id={`${provider.id}-key`}
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder={
              provider.has_api_key ? "Configured — leave blank to keep" : "Paste API key"
            }
            disabled={saving}
          />
        </div>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      {provider.provider_key === "lm_studio" ? (
        <p
          role="status"
          aria-live="polite"
          className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300"
        >
          {connectionState === "checking" ? (
            <Loader2 className="size-4 shrink-0 animate-spin" />
          ) : connectionState === "connected" ? (
            <CheckCircle2 className="size-4 shrink-0" />
          ) : (
            <CircleX className="size-4 shrink-0" />
          )}
          <span>
            <span className="font-medium">Connection status:</span>{" "}
            {connectionState === "checking"
              ? "Checking…"
              : connectionState === "connected"
                ? `Connected — ${connectionMessage}`
                : `Disconnected — ${connectionMessage}`}
          </span>
        </p>
      ) : null}

      {testResult ? (
        <p
          className={`flex items-center gap-2 text-sm ${
            testResult.ok ? "text-emerald-600 dark:text-emerald-400" : "text-destructive"
          }`}
        >
          {testResult.ok ? (
            <CheckCircle2 className="size-4 shrink-0" />
          ) : (
            <CircleX className="size-4 shrink-0" />
          )}
          {testResult.message}
        </p>
      ) : null}

      <div className="flex items-center justify-end gap-2">
        {!canTest ? (
          <p className="text-xs text-muted-foreground">Save a key first to test it.</p>
        ) : null}
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={testing || saving || !canTest}
          className="gap-2"
        >
          {testing ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <PlugZap className="size-4" />
          )}
          {testing ? "Testing…" : "Test connection"}
        </Button>
        <Button size="sm" onClick={handleSave} disabled={saving} className="gap-2">
          {saving ? <Loader2 className="size-4 animate-spin" /> : null}
          Save
        </Button>
      </div>
    </div>
  );
}
