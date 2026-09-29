"use client";

import { useState } from "react";
import { CheckCircle2, Loader2, Plus, Sparkles, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/api/client";
import { updateQuestion } from "@/lib/api/questions";
import type { Question, QuestionOptionInput, QuestionType } from "@/lib/api/types";

interface EditableOption {
  option_label: string;
  option_text: string;
  is_correct: boolean;
}

export function QuestionCard({
  paperId,
  question,
  onSaved,
}: {
  paperId: string;
  question: Question;
  onSaved: (updated: Question) => void;
}) {
  const [questionType, setQuestionType] = useState<QuestionType>(
    question.question_type,
  );
  const [promptText, setPromptText] = useState(question.prompt_text);
  const [explanationText, setExplanationText] = useState(
    question.explanation_text ?? "",
  );
  const [shortAnswerExpected, setShortAnswerExpected] = useState(
    question.short_answer_expected ?? "",
  );
  const [options, setOptions] = useState<EditableOption[]>(
    question.options.map((o) => ({
      option_label: o.option_label,
      option_text: o.option_text ?? "",
      is_correct: o.is_correct,
    })),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateOption(index: number, patch: Partial<EditableOption>) {
    setOptions((prev) => prev.map((o, i) => (i === index ? { ...o, ...patch } : o)));
  }

  function setCorrect(index: number) {
    setOptions((prev) => prev.map((o, i) => ({ ...o, is_correct: i === index })));
  }

  function addOption() {
    const nextLabel = String.fromCharCode(65 + options.length);
    setOptions((prev) => [
      ...prev,
      { option_label: nextLabel, option_text: "", is_correct: false },
    ]);
  }

  function removeOption(index: number) {
    setOptions((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const payloadOptions: QuestionOptionInput[] =
        questionType === "mcq"
          ? options.map((o, index) => ({
              option_label: o.option_label,
              option_text: o.option_text,
              is_correct: o.is_correct,
              display_order: index,
            }))
          : [];

      const updated = await updateQuestion(paperId, question.id, {
        question_type: questionType,
        prompt_text: promptText,
        explanation_text: explanationText || null,
        short_answer_expected:
          questionType === "short_answer" ? shortAnswerExpected || null : null,
        points: Number(question.points) || 1,
        options: payloadOptions,
      });
      onSaved(updated);
    } catch (err) {
      setError(getErrorMessage(err, "Could not save this question."));
    } finally {
      setSaving(false);
    }
  }

  const correctIndex = options.findIndex((o) => o.is_correct);

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <CardTitle className="text-base">Question {question.question_number}</CardTitle>
        {question.is_reviewed ? (
          <Badge className="gap-1">
            <CheckCircle2 className="size-3.5" />
            Reviewed
          </Badge>
        ) : (
          <Badge variant="secondary">Needs review</Badge>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-2">
          <Label>Question type</Label>
          <Select
            value={questionType}
            onValueChange={(value) => setQuestionType(value as QuestionType)}
          >
            <SelectTrigger className="w-full sm:w-56">
              <SelectValue>
                {(value: string | null) =>
                  value === "mcq" ? "Multiple choice" : "Short answer"
                }
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="mcq">Multiple choice</SelectItem>
              <SelectItem value="short_answer">Short answer</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2">
          <Label htmlFor={`${question.id}-prompt`}>Prompt</Label>
          <Textarea
            id={`${question.id}-prompt`}
            value={promptText}
            onChange={(event) => setPromptText(event.target.value)}
            rows={3}
          />
        </div>

        {questionType === "mcq" ? (
          <div className="grid gap-2">
            <Label>Answer options — select the correct one</Label>
            {question.llm_suggested_answer ? (
              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Sparkles className="size-3.5 shrink-0" />
                AI suggested option {question.llm_suggested_answer} — it may have
                used its own subject knowledge rather than an answer key in the
                source, so double-check before confirming.
              </p>
            ) : null}
            <RadioGroup
              value={String(correctIndex)}
              onValueChange={(value) => setCorrect(Number(value))}
              className="flex flex-col gap-2"
            >
              {options.map((option, index) => (
                <div key={index} className="flex items-center gap-2">
                  <RadioGroupItem
                    value={String(index)}
                    id={`${question.id}-opt-${index}`}
                  />
                  <Input
                    value={option.option_label}
                    onChange={(event) =>
                      updateOption(index, { option_label: event.target.value })
                    }
                    className="w-14 shrink-0 text-center"
                  />
                  <Input
                    value={option.option_text}
                    onChange={(event) =>
                      updateOption(index, { option_text: event.target.value })
                    }
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeOption(index)}
                    className="shrink-0 text-muted-foreground"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              ))}
            </RadioGroup>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addOption}
              className="w-fit gap-2"
            >
              <Plus className="size-3.5" />
              Add option
            </Button>
          </div>
        ) : (
          <div className="grid gap-2">
            <Label htmlFor={`${question.id}-expected`}>Model / expected answer</Label>
            <Textarea
              id={`${question.id}-expected`}
              value={shortAnswerExpected}
              onChange={(event) => setShortAnswerExpected(event.target.value)}
              rows={2}
              placeholder="What should count as a correct answer?"
            />
          </div>
        )}

        <div className="grid gap-2">
          <Label htmlFor={`${question.id}-explanation`}>
            Explanation (shown to students after they submit)
          </Label>
          <Textarea
            id={`${question.id}-explanation`}
            value={explanationText}
            onChange={(event) => setExplanationText(event.target.value)}
            rows={2}
          />
        </div>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </CardContent>
      <CardFooter className="justify-end">
        <Button onClick={handleSave} disabled={saving} className="gap-2">
          {saving ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <CheckCircle2 className="size-4" />
          )}
          {saving ? "Saving…" : "Save & confirm"}
        </Button>
      </CardFooter>
    </Card>
  );
}
