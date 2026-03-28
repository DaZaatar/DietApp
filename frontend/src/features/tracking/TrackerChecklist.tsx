import { useEffect, useMemo, useState } from "react";

import { getJson, patchJson, postForm } from "../../shared/lib/api";

type Status = "planned" | "eaten" | "skipped";

type IngredientRow = {
  name: string;
  quantity: string;
  unit: string;
  category: string;
};

type Item = {
  mealId: number;
  weekIndex: number;
  dayName: string;
  mealType: string;
  title: string;
  status: Status;
  notes: string | null;
  ingredients: IngredientRow[];
};

function sortForDisplay(items: Item[]): Item[] {
  return [...items]
    .map((item, index) => ({ item, index }))
    .sort((a, b) => {
      const pa = a.item.status === "planned" ? 0 : 1;
      const pb = b.item.status === "planned" ? 0 : 1;
      if (pa !== pb) return pa - pb;
      return a.index - b.index;
    })
    .map(({ item }) => item);
}

function cardSurfaceClass(status: Status): string {
  if (status === "eaten") {
    return "border-emerald-300 bg-emerald-50/60 shadow-sm";
  }
  if (status === "skipped") {
    return "border-amber-300 bg-amber-50/60 shadow-sm";
  }
  return "border-slate-200 bg-white";
}

function statusAccentClass(status: Status): string {
  if (status === "eaten") {
    return "bg-emerald-100 text-emerald-900 ring-1 ring-emerald-200";
  }
  if (status === "skipped") {
    return "bg-amber-100 text-amber-900 ring-1 ring-amber-200";
  }
  return "bg-slate-100 text-slate-700 ring-1 ring-slate-200";
}

export function TrackerChecklist() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyMealId, setBusyMealId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const displayItems = useMemo(() => sortForDisplay(items), [items]);

  useEffect(() => {
    let active = true;
    async function loadMeals() {
      setLoading(true);
      setError(null);
      try {
        const data = await getJson<
          Array<{
            meal_id: number;
            week_index: number;
            day_name: string;
            meal_type: string;
            title: string;
            status: Status;
            notes: string | null;
            ingredients: IngredientRow[];
          }>
        >("/tracking/meals");
        if (!active) return;
        setItems(
          data.map((item) => ({
            mealId: item.meal_id,
            weekIndex: item.week_index,
            dayName: item.day_name,
            mealType: item.meal_type,
            title: item.title,
            status: item.status,
            notes: item.notes,
            ingredients: item.ingredients ?? [],
          })),
        );
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load meals");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadMeals();
    return () => {
      active = false;
    };
  }, []);

  async function setStatus(mealId: number, status: Status) {
    setBusyMealId(mealId);
    setMessage(null);
    setError(null);
    try {
      await patchJson(`/tracking/meals/${mealId}`, { status });
      setItems((prev) => prev.map((item) => (item.mealId === mealId ? { ...item, status } : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    } finally {
      setBusyMealId(null);
    }
  }

  async function attachImage(mealId: number, file: File | null) {
    if (!file) return;
    setBusyMealId(mealId);
    setMessage(null);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await postForm(`/tracking/meals/${mealId}/attachments`, formData);
      setMessage("Meal image attached.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Image upload failed");
    } finally {
      setBusyMealId(null);
    }
  }

  return (
    <section className="space-y-4">
      <p className="text-sm text-slate-600">Quick meal checklist optimized for phone interaction.</p>
      {loading && <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700">Loading meals...</p>}
      {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      {message && <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700">{message}</p>}
      <ul className="space-y-3">
        {displayItems.map((item) => (
          <li key={item.mealId} className={`rounded-xl border p-4 ${cardSurfaceClass(item.status)}`}>
            <p className="text-sm font-medium capitalize text-slate-900">
              {item.mealType}: {item.title}
            </p>
            <p className="mt-1 text-xs text-slate-600">
              Week {item.weekIndex} - {item.dayName}
            </p>
            <p className="mt-2">
              <span
                className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize tracking-wide ${statusAccentClass(item.status)}`}
              >
                {item.status}
              </span>
            </p>

            {(item.ingredients.length > 0 || item.notes) && (
              <details className="mt-3 rounded-lg border border-slate-200/80 bg-white/70 p-3 open:shadow-inner">
                <summary className="cursor-pointer select-none text-xs font-medium text-slate-800">
                  Ingredients
                  {item.ingredients.length > 0 ? ` (${item.ingredients.length})` : ""}
                  {item.notes ? " & notes" : ""}
                </summary>
                {item.ingredients.length > 0 && (
                  <ul className="mt-2 space-y-1.5 text-xs text-slate-700">
                    {item.ingredients.map((ing, idx) => (
                      <li key={`${ing.name}-${idx}`} className="flex flex-wrap gap-x-1 border-b border-slate-100 pb-1.5 last:border-0 last:pb-0">
                        <span className="font-medium text-slate-900">
                          {ing.quantity} {ing.unit}
                        </span>
                        <span>{ing.name}</span>
                        <span className="text-slate-500">· {ing.category}</span>
                      </li>
                    ))}
                  </ul>
                )}
                {item.notes && (
                  <p className={`text-xs text-slate-600 ${item.ingredients.length > 0 ? "mt-2" : "mt-1"}`}>
                    <span className="font-medium text-slate-700">Notes: </span>
                    {item.notes}
                  </p>
                )}
              </details>
            )}

            <div className="mt-3 grid grid-cols-3 gap-2">
              <button
                className="rounded-md border border-slate-300 px-2 py-2 text-xs"
                onClick={() => setStatus(item.mealId, "planned")}
                disabled={busyMealId === item.mealId}
              >
                Planned
              </button>
              <button
                className="rounded-md border border-emerald-300 bg-emerald-50 px-2 py-2 text-xs text-emerald-700"
                onClick={() => setStatus(item.mealId, "eaten")}
                disabled={busyMealId === item.mealId}
              >
                Eaten
              </button>
              <button
                className="rounded-md border border-amber-300 bg-amber-50 px-2 py-2 text-xs text-amber-700"
                onClick={() => setStatus(item.mealId, "skipped")}
                disabled={busyMealId === item.mealId}
              >
                Skipped
              </button>
            </div>
            <label className="mt-3 block text-xs text-slate-600">
              Attach meal image
              <input
                className="mt-1 block w-full text-xs"
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) => attachImage(item.mealId, e.target.files?.[0] ?? null)}
              />
            </label>
          </li>
        ))}
      </ul>
      {!loading && items.length === 0 && (
        <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700">No meals found for tracking.</p>
      )}
    </section>
  );
}
