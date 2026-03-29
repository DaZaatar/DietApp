import { useEffect, useRef, useState } from "react";

import { postForm, postJson } from "../../shared/lib/api";
import type { MealPlanPreview } from "./types";

const DRAFT_KEY = "dietapp_import_draft_v1";

function todayInputValue(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

type Draft = { preview: MealPlanPreview; startsOn: string };

function loadDraft(): Draft | null {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Draft;
    if (!parsed?.preview?.weeks) return null;
    return parsed;
  } catch {
    return null;
  }
}

function saveDraft(preview: MealPlanPreview, startsOn: string): void {
  try {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ preview, startsOn }));
  } catch {
    /* quota / private mode */
  }
}

function clearDraft(): void {
  sessionStorage.removeItem(DRAFT_KEY);
}

export function ImportFlow() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [startsOn, setStartsOn] = useState(todayInputValue);
  const [preview, setPreview] = useState<MealPlanPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [commitMessage, setCommitMessage] = useState<string | null>(null);
  const [restored, setRestored] = useState(false);

  useEffect(() => {
    const d = loadDraft();
    if (d) {
      setPreview(d.preview);
      setStartsOn(d.startsOn);
      setRestored(true);
    }
  }, []);

  useEffect(() => {
    if (preview) {
      saveDraft(preview, startsOn);
    }
  }, [preview, startsOn]);

  function clearFileInput() {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  async function onPreview() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setCommitMessage(null);
    setRestored(false);
    try {
      const data = new FormData();
      data.append("file", file);
      const result = await postForm<MealPlanPreview>("/imports/preview", data);
      setPreview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import preview failed");
    } finally {
      setLoading(false);
    }
  }

  async function onCommit() {
    if (!preview) return;
    setLoading(true);
    setError(null);
    try {
      const result = await postJson<{ meal_plan_id: number; name: string }>("/imports/commit", {
        ...preview,
        starts_on: startsOn,
      });
      setCommitMessage(`Saved meal plan #${result.meal_plan_id} (${result.name})`);
      setPreview(null);
      clearDraft();
      clearFileInput();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Commit failed");
    } finally {
      setLoading(false);
    }
  }

  function discardDraft() {
    setPreview(null);
    clearDraft();
    clearFileInput();
    setCommitMessage(null);
    setError(null);
    setRestored(false);
  }

  return (
    <section className="space-y-4">
      {restored && preview && (
        <p className="rounded-lg border border-brand-600/30 bg-brand-50/80 px-3 py-2 text-sm text-brand-700 dark:border-brand-500/40 dark:bg-brand-950/40 dark:text-brand-100">
          Restored your last preview from this session. You can save it or discard below.
        </p>
      )}
      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200">
          Upload bi-weekly meal plan (PDF)
        </label>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-4">
          <div className="min-w-0 flex-1">
            <label htmlFor="import-pdf-input" className="sr-only">
              Choose PDF file
            </label>
            <input
              id="import-pdf-input"
              ref={fileInputRef}
              className="sr-only"
              type="file"
              accept="application/pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
              <button
                type="button"
                className="inline-flex w-full shrink-0 items-center justify-center rounded-lg border border-slate-300 bg-slate-50 px-4 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 sm:w-auto"
                onClick={() => fileInputRef.current?.click()}
              >
                Choose PDF…
              </button>
              <span className="truncate text-sm text-slate-600 dark:text-slate-400">
                {file ? file.name : "No file selected"}
              </span>
            </div>
          </div>
          <div className="shrink-0 sm:min-w-[11rem]">
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400" htmlFor="plan-start-date">
              Plan starts on
            </label>
            <input
              id="plan-start-date"
              type="date"
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
              value={startsOn}
              onChange={(e) => setStartsOn(e.target.value)}
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">Week 1 day 1 uses this date; each day +1.</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onPreview}
          disabled={!file || loading}
          className="mt-4 w-full rounded-lg bg-brand-600 px-4 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700 disabled:opacity-50 sm:w-auto"
        >
          {loading ? "Parsing..." : "Preview Import"}
        </button>
      </div>

      {error && (
        <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-800 dark:bg-rose-950/50 dark:text-rose-200">{error}</p>
      )}
      {commitMessage && (
        <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200">
          {commitMessage}
        </p>
      )}

      {preview && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{preview.name}</h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Review parsed meals, then save.</p>
              </div>
              <div className="flex w-full flex-col gap-2 sm:w-auto sm:shrink-0 sm:flex-row">
                <button
                  type="button"
                  onClick={discardDraft}
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm font-medium text-slate-800 dark:border-slate-600 dark:text-slate-200 sm:w-auto"
                >
                  Discard
                </button>
                <button
                  type="button"
                  onClick={onCommit}
                  disabled={loading}
                  className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-50 dark:bg-brand-600 dark:hover:bg-brand-700 sm:w-auto"
                >
                  Save Meal Plan
                </button>
              </div>
            </div>
          </div>
          <div className="grid gap-4">
            {preview.weeks.map((week) => (
              <article
                key={week.week_index}
                className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
              >
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Week {week.week_index}</h3>
                <div className="mt-3 grid gap-3">
                  {week.days.map((day) => (
                    <div key={day.day} className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800/60">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{day.day}</p>
                      <ul className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-300">
                        {day.meals.map((meal, idx) => (
                          <li key={`${meal.title}-${idx}`}>
                            <span className="font-medium capitalize">{meal.meal_type}:</span> {meal.title}
                            {meal.ingredients.length > 0 && (
                              <ul className="ml-4 mt-1 list-disc text-xs text-slate-600 dark:text-slate-400">
                                {meal.ingredients.map((ingredient, ingredientIdx) => (
                                  <li key={`${ingredient.name}-${ingredientIdx}`}>
                                    {ingredient.quantity} {ingredient.unit} {ingredient.name} ({ingredient.category})
                                  </li>
                                ))}
                              </ul>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
