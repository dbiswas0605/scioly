"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getErrorMessage } from "@/lib/api/client";
import { updateAppSetting } from "@/lib/api/admin";
import type { AppSetting } from "@/lib/api/types";

const DEFAULT_MINUTES = 30;
const SETTING_KEY = "default_exam_duration_minutes";

export function TimerSettings({ setting }: { setting: AppSetting | undefined }) {
  const initialMinutes = setting?.value ? Number(setting.value) : DEFAULT_MINUTES;
  const [minutes, setMinutes] = useState(String(initialMinutes));
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    const parsed = Number(minutes);
    if (!Number.isInteger(parsed) || parsed <= 0) {
      setError("Enter a whole number of minutes greater than 0.");
      return;
    }
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await updateAppSetting(SETTING_KEY, {
        value: String(parsed),
        value_type: "integer",
      });
      setSaved(true);
    } catch (err) {
      setError(getErrorMessage(err, "Could not save the default timer."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-end gap-2">
        <div className="grid gap-1.5">
          <Label htmlFor="default-duration">Default exam duration (minutes)</Label>
          <Input
            id="default-duration"
            type="number"
            min={1}
            max={480}
            value={minutes}
            onChange={(event) => {
              setMinutes(event.target.value);
              setSaved(false);
            }}
            disabled={saving}
            className="w-32"
          />
        </div>
        <Button onClick={handleSave} disabled={saving} size="sm" className="gap-2">
          {saving ? <Loader2 className="size-4 animate-spin" /> : null}
          {saving ? "Saving…" : "Save"}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">
        Applied to new question papers when they&apos;re uploaded. Each
        paper&apos;s timer can still be changed individually afterward under
        Question Papers below.
      </p>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {saved ? <p className="text-sm text-emerald-600 dark:text-emerald-400">Saved.</p> : null}
    </div>
  );
}
