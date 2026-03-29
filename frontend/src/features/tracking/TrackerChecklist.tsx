import { useCallback, useEffect, useMemo, useState } from "react";

import { getJson, patchJson, postForm, postJson } from "../../shared/lib/api";

type Status = "planned" | "eaten" | "skipped";

type IngredientRow = {
  name: string;
  quantity: string;
  unit: string;
  category: string;
};

type Item = {
  mealId: number;
  dayId: number;
  weekIndex: number;
  dayName: string;
  dayIndex: number;
  planStartsOn: string | null;
  mealType: string;
  title: string;
  status: Status;
  notes: string | null;
  ingredients: IngredientRow[];
};

type DayGroup = {
  key: string;
  dayId: number;
  weekIndex: number;
  dayName: string;
  dayIndex: number;
  planStartsOn: string | null;
  meals: Item[];
};

function mealOptionLabel(item: Item): string {
  return `W${item.weekIndex} ${item.dayName} · ${item.mealType}: ${item.title}`;
}

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

function buildDayGroups(items: Item[]): DayGroup[] {
  const map = new Map<string, Item[]>();
  for (const item of items) {
    const key = `${item.weekIndex}-${item.dayIndex}`;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(item);
  }
  const keys = Array.from(map.keys()).sort((a, b) => {
    const [wa, da] = a.split("-").map(Number);
    const [wb, db] = b.split("-").map(Number);
    if (wa !== wb) return wa - wb;
    return da - db;
  });
  return keys.map((key) => {
    const meals = sortForDisplay(map.get(key)!);
    const first = meals[0];
    return {
      key,
      dayId: first.dayId,
      weekIndex: first.weekIndex,
      dayName: first.dayName,
      dayIndex: first.dayIndex,
      planStartsOn: first.planStartsOn,
      meals,
    };
  });
}

function calendarLabel(planStartsOn: string | null, dayIndex: number): string | null {
  if (!planStartsOn) return null;
  const base = new Date(`${planStartsOn}T12:00:00`);
  if (Number.isNaN(base.getTime())) return null;
  base.setDate(base.getDate() + dayIndex);
  return base.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

function cardSurfaceClass(status: Status): string {
  if (status === "eaten") {
    return "border-emerald-300 bg-emerald-50/60 shadow-sm dark:border-emerald-700 dark:bg-emerald-950/40";
  }
  if (status === "skipped") {
    return "border-amber-300 bg-amber-50/60 shadow-sm dark:border-amber-700 dark:bg-amber-950/40";
  }
  return "border-slate-200 bg-white dark:border-slate-600 dark:bg-slate-800/80";
}

function statusAccentClass(status: Status): string {
  if (status === "eaten") {
    return "bg-emerald-100 text-emerald-900 ring-1 ring-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-100 dark:ring-emerald-800";
  }
  if (status === "skipped") {
    return "bg-amber-100 text-amber-900 ring-1 ring-amber-200 dark:bg-amber-900/50 dark:text-amber-100 dark:ring-amber-800";
  }
  return "bg-slate-100 text-slate-700 ring-1 ring-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:ring-slate-600";
}

type SwapModal =
  | null
  | { kind: "meal"; source: Item }
  | { kind: "day"; group: DayGroup; label: string };

export function TrackerChecklist() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyMealId, setBusyMealId] = useState<number | null>(null);
  const [swapBusy, setSwapBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [swapModal, setSwapModal] = useState<SwapModal>(null);
  const [swapTargetId, setSwapTargetId] = useState("");

  const dayGroups = useMemo(() => buildDayGroups(items), [items]);

  const loadMeals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getJson<
        Array<{
          meal_id: number;
          day_id: number;
          week_index: number;
          day_name: string;
          day_index: number;
          plan_starts_on: string | null;
          meal_type: string;
          title: string;
          status: Status;
          notes: string | null;
          ingredients: IngredientRow[];
        }>
      >("/tracking/meals");
      setItems(
        data.map((item) => ({
          mealId: item.meal_id,
          dayId: item.day_id,
          weekIndex: item.week_index,
          dayName: item.day_name,
          dayIndex: item.day_index ?? 0,
          planStartsOn: item.plan_starts_on ?? null,
          mealType: item.meal_type,
          title: item.title,
          status: item.status,
          notes: item.notes,
          ingredients: item.ingredients ?? [],
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load meals");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMeals();
  }, [loadMeals]);

  function openMealSwap(source: Item) {
    const others = items.filter((i) => i.mealId !== source.mealId);
    if (others.length === 0) {
      setError("No other meals in this plan to swap with.");
      return;
    }
    setError(null);
    setSwapModal({ kind: "meal", source });
    setSwapTargetId(String(others[0]!.mealId));
  }

  function openDaySwap(group: DayGroup) {
    const others = dayGroups.filter((g) => g.dayId !== group.dayId);
    if (others.length === 0) {
      setError("No other days in this plan to swap with.");
      return;
    }
    const dateLine = calendarLabel(group.planStartsOn, group.dayIndex);
    const label = dateLine
      ? `Week ${group.weekIndex} · ${group.dayName} (${dateLine})`
      : `Week ${group.weekIndex} · ${group.dayName}`;
    setError(null);
    setSwapModal({ kind: "day", group, label });
    setSwapTargetId(String(others[0]!.dayId));
  }

  async function confirmSwap() {
    if (!swapModal) return;
    setSwapBusy(true);
    setError(null);
    setMessage(null);
    try {
      if (swapModal.kind === "meal") {
        const b = Number(swapTargetId);
        if (!Number.isFinite(b)) throw new Error("Pick a meal to swap with.");
        await postJson("/tracking/swap/meals", {
          meal_id_a: swapModal.source.mealId,
          meal_id_b: b,
        });
      } else {
        const b = Number(swapTargetId);
        if (!Number.isFinite(b)) throw new Error("Pick a day to swap with.");
        await postJson("/tracking/swap/days", {
          day_id_a: swapModal.group.dayId,
          day_id_b: b,
        });
      }
      setSwapModal(null);
      setMessage(swapModal.kind === "meal" ? "Meals swapped." : "Days swapped.");
      await loadMeals();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Swap failed");
    } finally {
      setSwapBusy(false);
    }
  }

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

  const mealSwapChoices =
    swapModal?.kind === "meal" ? items.filter((i) => i.mealId !== swapModal.source.mealId) : [];
  const daySwapChoices =
    swapModal?.kind === "day" ? dayGroups.filter((g) => g.dayId !== swapModal.group.dayId) : [];

  return (
    <section className="space-y-4">
      <p className="text-sm text-slate-600 dark:text-slate-400">Quick meal checklist optimized for phone interaction.</p>
      {loading && (
        <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          Loading meals...
        </p>
      )}
      {error && (
        <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-800 dark:bg-rose-950/50 dark:text-rose-200">{error}</p>
      )}
      {message && (
        <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-300">{message}</p>
      )}
      <ul className="space-y-4">
        {dayGroups.map((group) => {
          const dateLine = calendarLabel(group.planStartsOn, group.dayIndex);
          const canDaySwap = dayGroups.length > 1;
          return (
            <li
              key={group.key}
              className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50/80 dark:border-slate-700 dark:bg-slate-900/50"
            >
              <div className="flex flex-col gap-2 border-b border-slate-200 bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-slate-700 dark:bg-slate-900">
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    Week {group.weekIndex} · {group.dayName}
                  </p>
                  {dateLine && <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">{dateLine}</p>}
                </div>
                <button
                  type="button"
                  className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-800 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:text-slate-200"
                  disabled={!canDaySwap || swapBusy}
                  title={
                    canDaySwap
                      ? "Swap this day’s meals with another day (same number of meals per day)"
                      : "Need at least two days in the plan"
                  }
                  onClick={() => openDaySwap(group)}
                >
                  Swap day
                </button>
              </div>
              <ul className="space-y-3 p-3">
                {group.meals.map((item) => (
                  <li key={item.mealId} className={`rounded-xl border p-4 ${cardSurfaceClass(item.status)}`}>
                    <p className="text-sm font-medium capitalize text-slate-900 dark:text-slate-100">
                      {item.mealType}: {item.title}
                    </p>
                    <p className="mt-2">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize tracking-wide ${statusAccentClass(item.status)}`}
                      >
                        {item.status}
                      </span>
                    </p>

                    {(item.ingredients.length > 0 || item.notes) && (
                      <details className="mt-3 rounded-lg border border-slate-200/80 bg-white/70 p-3 open:shadow-inner dark:border-slate-600 dark:bg-slate-900/40">
                        <summary className="cursor-pointer select-none text-xs font-medium text-slate-800 dark:text-slate-200">
                          Ingredients
                          {item.ingredients.length > 0 ? ` (${item.ingredients.length})` : ""}
                          {item.notes ? " & notes" : ""}
                        </summary>
                        {item.ingredients.length > 0 && (
                          <ul className="mt-2 space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                            {item.ingredients.map((ing, idx) => (
                              <li
                                key={`${ing.name}-${idx}`}
                                className="flex flex-wrap gap-x-1 border-b border-slate-100 pb-1.5 last:border-0 last:pb-0 dark:border-slate-600"
                              >
                                <span className="font-medium text-slate-900 dark:text-slate-100">
                                  {ing.quantity} {ing.unit}
                                </span>
                                <span>{ing.name}</span>
                                <span className="text-slate-500 dark:text-slate-500">· {ing.category}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                        {item.notes && (
                          <p
                            className={`text-xs text-slate-600 dark:text-slate-400 ${item.ingredients.length > 0 ? "mt-2" : "mt-1"}`}
                          >
                            <span className="font-medium text-slate-700 dark:text-slate-300">Notes: </span>
                            {item.notes}
                          </p>
                        )}
                      </details>
                    )}

                    <div className="mt-3 grid grid-cols-3 gap-2">
                      <button
                        className="rounded-md border border-slate-300 px-2 py-2 text-xs dark:border-slate-600 dark:text-slate-200"
                        onClick={() => setStatus(item.mealId, "planned")}
                        disabled={busyMealId === item.mealId || swapBusy}
                      >
                        Planned
                      </button>
                      <button
                        className="rounded-md border border-emerald-300 bg-emerald-50 px-2 py-2 text-xs text-emerald-700 dark:border-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-200"
                        onClick={() => setStatus(item.mealId, "eaten")}
                        disabled={busyMealId === item.mealId || swapBusy}
                      >
                        Eaten
                      </button>
                      <button
                        className="rounded-md border border-amber-300 bg-amber-50 px-2 py-2 text-xs text-amber-700 dark:border-amber-700 dark:bg-amber-950/50 dark:text-amber-200"
                        onClick={() => setStatus(item.mealId, "skipped")}
                        disabled={busyMealId === item.mealId || swapBusy}
                      >
                        Skipped
                      </button>
                    </div>
                    <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <label className="block text-xs text-slate-600 dark:text-slate-400 sm:flex-1">
                        Attach meal image
                        <input
                          className="mt-1 block w-full text-xs text-slate-800 file:mr-2 file:rounded file:border-0 file:bg-slate-200 file:px-2 file:py-1 dark:text-slate-200 dark:file:bg-slate-700"
                          type="file"
                          accept="image/*"
                          capture="environment"
                          disabled={swapBusy}
                          onChange={(e) => attachImage(item.mealId, e.target.files?.[0] ?? null)}
                        />
                      </label>
                      <button
                        type="button"
                        className="shrink-0 rounded-md border border-slate-300 px-3 py-2 text-xs font-medium text-slate-800 dark:border-slate-600 dark:text-slate-200"
                        disabled={items.length < 2 || swapBusy}
                        title={items.length < 2 ? "Need at least two meals in the plan" : "Swap planned meal with another slot"}
                        onClick={() => openMealSwap(item)}
                      >
                        Swap meal
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ul>
      {!loading && items.length === 0 && (
        <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          No meals found for tracking.
        </p>
      )}

      {swapModal && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="swap-dialog-title"
          onClick={() => !swapBusy && setSwapModal(null)}
        >
          <div
            className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 shadow-xl dark:border-slate-600 dark:bg-slate-900"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="swap-dialog-title" className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {swapModal.kind === "meal" ? "Swap with which meal?" : "Swap with which day?"}
            </h3>
            {swapModal.kind === "meal" ? (
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Your slot: <span className="font-medium text-slate-800 dark:text-slate-200">{mealOptionLabel(swapModal.source)}</span>
              </p>
            ) : (
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Your day: <span className="font-medium text-slate-800 dark:text-slate-200">{swapModal.label}</span>
              </p>
            )}
            <label className="mt-4 block text-xs font-medium text-slate-700 dark:text-slate-300">
              {swapModal.kind === "meal" ? "Swap with" : "Swap with"}
              <select
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                value={swapTargetId}
                onChange={(e) => setSwapTargetId(e.target.value)}
              >
                {swapModal.kind === "meal"
                  ? mealSwapChoices.map((i) => (
                      <option key={i.mealId} value={String(i.mealId)}>
                        {mealOptionLabel(i)}
                      </option>
                    ))
                  : daySwapChoices.map((g) => {
                      const dl = calendarLabel(g.planStartsOn, g.dayIndex);
                      const lab = dl ? `Week ${g.weekIndex} · ${g.dayName} (${dl})` : `Week ${g.weekIndex} · ${g.dayName}`;
                      return (
                        <option key={g.dayId} value={String(g.dayId)}>
                          {lab} · {g.meals.length} meal{g.meals.length === 1 ? "" : "s"}
                        </option>
                      );
                    })}
              </select>
            </label>
            {swapModal.kind === "day" && (
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
                Both days must have the same number of meals; meals are paired in stable order to swap plans.
              </p>
            )}
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-800 dark:border-slate-600 dark:text-slate-200"
                onClick={() => setSwapModal(null)}
                disabled={swapBusy}
              >
                Cancel
              </button>
              <button
                type="button"
                className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white dark:bg-brand-600"
                onClick={() => void confirmSwap()}
                disabled={swapBusy}
              >
                {swapBusy ? "Swapping…" : "Confirm swap"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
