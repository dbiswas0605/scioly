"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Loader2, TriangleAlert, UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { getErrorMessage } from "@/lib/api/client";
import { uploadPaper } from "@/lib/api/papers";
import { createSubject } from "@/lib/api/subjects";
import type { Subject } from "@/lib/api/types";

const ADD_NEW_SUBJECT_VALUE = "__add_new_subject__";

export function UploadForm({ subjects: initialSubjects }: { subjects: Subject[] }) {
  const router = useRouter();
  const [subjects, setSubjects] = useState(initialSubjects);
  const [subjectId, setSubjectId] = useState<string>("");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [addingSubject, setAddingSubject] = useState(false);
  const [newSubjectName, setNewSubjectName] = useState("");
  const [creatingSubject, setCreatingSubject] = useState(false);
  const [subjectError, setSubjectError] = useState<string | null>(null);

  const canSubmit = subjectId && title.trim() && file && !submitting;

  function handleSubjectSelect(value: string | null) {
    if (!value) return;
    if (value === ADD_NEW_SUBJECT_VALUE) {
      setSubjectError(null);
      setAddingSubject(true);
      return;
    }
    setSubjectId(value);
  }

  async function handleCreateSubject() {
    const trimmed = newSubjectName.trim();
    if (!trimmed) return;
    setCreatingSubject(true);
    setSubjectError(null);
    try {
      const created = await createSubject(trimmed);
      setSubjects((prev) =>
        [...prev, created].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setSubjectId(created.id);
      setAddingSubject(false);
      setNewSubjectName("");
    } catch (err) {
      setSubjectError(getErrorMessage(err, "Could not create the subject."));
    } finally {
      setCreatingSubject(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file || !subjectId || !title.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("subject_id", subjectId);
      formData.append("title", title.trim());
      formData.append("file", file);

      const paper = await uploadPaper(formData);
      router.push(`/papers/${paper.id}`);
    } catch (err) {
      setError(getErrorMessage(err, "Upload failed — is the backend running?"));
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <div className="grid gap-2">
        <Label htmlFor="subject">Subject</Label>
        {addingSubject ? (
          <div className="flex flex-wrap items-center gap-2">
            <Input
              autoFocus
              value={newSubjectName}
              onChange={(event) => setNewSubjectName(event.target.value)}
              placeholder="New subject name"
              disabled={creatingSubject}
              className="w-full sm:w-72"
            />
            <Button
              type="button"
              size="sm"
              onClick={handleCreateSubject}
              disabled={creatingSubject || !newSubjectName.trim()}
              className="gap-2"
            >
              {creatingSubject ? <Loader2 className="size-4 animate-spin" /> : null}
              Add
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setAddingSubject(false);
                setNewSubjectName("");
                setSubjectError(null);
              }}
              disabled={creatingSubject}
            >
              Cancel
            </Button>
          </div>
        ) : (
          <Select value={subjectId} onValueChange={handleSubjectSelect} disabled={submitting}>
            <SelectTrigger id="subject" className="w-full sm:w-80">
              <SelectValue>
                {(value: string | null) =>
                  (value && subjects.find((s) => s.id === value)?.name) ||
                  "Select a subject"
                }
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {subjects.map((subject) => (
                <SelectItem key={subject.id} value={subject.id}>
                  {subject.name}
                </SelectItem>
              ))}
              {subjects.length > 0 ? <SelectSeparator /> : null}
              <SelectItem value={ADD_NEW_SUBJECT_VALUE}>+ Add new subject</SelectItem>
            </SelectContent>
          </Select>
        )}
        {subjectError ? (
          <p className="text-sm text-destructive">{subjectError}</p>
        ) : null}
      </div>

      <div className="grid gap-2">
        <Label htmlFor="paper-title">Title</Label>
        <Input
          id="paper-title"
          placeholder="e.g. Anatomy & Physiology — Regional 2026"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          disabled={submitting}
          className="w-full sm:w-96"
        />
      </div>

      <div className="grid gap-2">
        <Label htmlFor="paper-file">Question paper file</Label>
        <Input
          id="paper-file"
          type="file"
          accept=".pdf,.doc,.docx,.txt,image/*"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          disabled={submitting}
          className="w-full sm:w-96"
        />
        <p className="text-xs text-muted-foreground">
          PDF, DOCX, TXT, or image files. (Legacy .doc isn&apos;t supported yet —
          use .docx or PDF instead.)
        </p>
      </div>

      {error ? (
        <p className="flex items-center gap-2 text-sm text-destructive">
          <TriangleAlert className="size-4 shrink-0" />
          {error}
        </p>
      ) : null}

      <Separator />

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={!canSubmit} className="gap-2">
          {submitting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <UploadCloud className="size-4" />
          )}
          {submitting ? "Uploading…" : "Upload"}
        </Button>
        <p className="text-xs text-muted-foreground">
          You&apos;ll review and confirm the parsed questions on the next screen.
        </p>
      </div>
    </form>
  );
}
