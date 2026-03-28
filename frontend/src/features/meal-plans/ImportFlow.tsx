import { useRef, useState } from "react";

import { postForm, postJson } from "../../shared/lib/api";
import type { MealPlanPreview } from "./types";

export function ImportFlow() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<MealPlanPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [commitMessage, setCommitMessage] = useState<string | null>(null);

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
      const result = await postJson<{ meal_plan_id: number; name: string }>("/imports/commit", preview);
      setCommitMessage(`Saved meal plan #${result.meal_plan_id} (${result.name})`);
      setPreview(null);
      clearFileInput();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Commit failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <label className="mb-2 block text-sm font-medium text-slate-700">Upload bi-weekly meal plan (PDF)</label>
        <input
          ref={fileInputRef}
          className="block w-full text-sm"
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button
          type="button"
          onClick={onPreview}
          disabled={!file || loading}
          className="mt-4 w-full rounded-lg bg-brand-600 px-4 py-3 text-sm font-medium text-white disabled:opacity-50 sm:w-auto"
        >
          {loading ? "Parsing..." : "Preview Import"}
        </button>
      </div>

      {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      {commitMessage && <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{commitMessage}</p>}

      {preview && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-base font-semibold text-slate-900">{preview.name}</h2>
                <p className="mt-1 text-sm text-slate-600">Review parsed meals, then save.</p>
              </div>
              <button
                type="button"
                onClick={onCommit}
                disabled={loading}
                className="w-full shrink-0 rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-50 sm:w-auto"
              >
                Save Meal Plan
              </button>
            </div>
          </div>
          <div className="grid gap-4">
            {preview.weeks.map((week) => (
              <article key={week.week_index} className="rounded-xl border border-slate-200 bg-white p-4">
                <h3 className="text-sm font-semibold text-slate-800">Week {week.week_index}</h3>
                <div className="mt-3 grid gap-3">
                  {week.days.map((day) => (
                    <div key={day.day} className="rounded-lg bg-slate-50 p-3">
                      <p className="text-sm font-medium text-slate-800">{day.day}</p>
                      <ul className="mt-2 space-y-1 text-sm text-slate-700">
                        {day.meals.map((meal, idx) => (
                          <li key={`${meal.title}-${idx}`}>
                            <span className="font-medium capitalize">{meal.meal_type}:</span> {meal.title}
                            {meal.ingredients.length > 0 && (
                              <ul className="ml-4 mt-1 list-disc text-xs text-slate-600">
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
