"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, MessageSquareText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/api/client";
import { updateAppSetting } from "@/lib/api/admin";
import type { AppSetting } from "@/lib/api/types";

interface ParsePromptSettingsProps {
  setting: AppSetting | undefined;
  settingKey: string;
  defaultPrompt: string;
  buttonLabel: string;
  dialogTitle: string;
  fieldLabel: string;
  description: string;
  savedMessage: string;
}

export function ParsePromptSettings({
  setting,
  settingKey,
  defaultPrompt,
  buttonLabel,
  dialogTitle,
  fieldLabel,
  description,
  savedMessage,
}: ParsePromptSettingsProps) {
  const [prompt, setPrompt] = useState(setting?.value ?? defaultPrompt);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  async function handleSave() {
    if (!prompt.trim()) {
      setError("Enter a prompt before saving.");
      return;
    }

    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await updateAppSetting(settingKey, {
        value: prompt,
        value_type: "string",
      });
      setSaved(true);
    } catch (err) {
      setError(getErrorMessage(err, "Could not save the parsing prompt."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Button
        variant="outline"
        className="gap-2"
        onClick={() => {
          setError(null);
          setSaved(false);
          setOpen(true);
        }}
      >
        <MessageSquareText className="size-4" />
        {buttonLabel}
      </Button>

      <dialog
        ref={dialogRef}
        aria-labelledby={`${settingKey}-title`}
        onClose={() => setOpen(false)}
        className="m-auto w-[calc(100%-2rem)] max-w-3xl rounded-xl border bg-background p-0 text-foreground shadow-xl backdrop:bg-black/50"
      >
        <div className="flex max-h-[85vh] flex-col">
          <div className="border-b p-6">
            <h2 id={`${settingKey}-title`} className="text-lg font-semibold">
              {dialogTitle}
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          </div>

          <div className="grid gap-2 overflow-y-auto p-6">
            <label htmlFor={settingKey} className="text-sm font-medium">
              {fieldLabel}
            </label>
            <Textarea
              id={settingKey}
              value={prompt}
              onChange={(event) => {
                setPrompt(event.target.value);
                setSaved(false);
              }}
              disabled={saving}
              rows={12}
              className="min-h-64 resize-y font-mono text-sm"
              spellCheck
            />
            <p className="text-xs text-muted-foreground">
              Enter plain text. The structured output format required by the
              parser remains enforced.
            </p>
            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
            {saved ? (
              <p
                role="status"
                className="text-sm text-emerald-600 dark:text-emerald-400"
              >
                {savedMessage}
              </p>
            ) : null}
          </div>

          <div className="flex flex-col-reverse justify-end gap-2 border-t bg-muted/30 p-4 sm:flex-row">
            <Button
              type="button"
              variant="outline"
              onClick={() => dialogRef.current?.close()}
              disabled={saving}
            >
              Close
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="gap-2"
            >
              {saving ? <Loader2 className="size-4 animate-spin" /> : null}
              {saving ? "Saving…" : "Save prompt"}
            </Button>
          </div>
        </div>
      </dialog>
    </>
  );
}
