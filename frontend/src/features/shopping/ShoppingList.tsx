import { useCallback, useEffect, useState } from "react";

import { deleteJson, getJson, patchJson } from "../../shared/lib/api";

type ShoppingItem = {
  id: string;
  category: string;
  name: string;
  quantity: string;
  unit: string;
  checked: boolean;
};

type ShoppingListResponse = {
  meal_plan_id: number;
  meal_plan_name: string;
  generated_at: string;
  items: ShoppingItem[];
};

type MealPlanSummary = {
  id: number;
  name: string;
  created_at: string;
};

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { dateStyle: "medium" });
  } catch {
    return iso;
  }
}

type CardProps = {
  mealPlanId: number;
  mealPlanName: string;
  createdAt: string;
  defaultExpanded: boolean;
  onDeleted: () => void;
};

function ShoppingListCard({ mealPlanId, mealPlanName, createdAt, defaultExpanded, onDeleted }: CardProps) {
  const [data, setData] = useState<ShoppingListResponse | null>(null);
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [loading, setLoading] = useState(true);
  const [loadingDelete, setLoadingDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<Set<string>>(() => new Set());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getJson<ShoppingListResponse>(`/shopping/list?meal_plan_id=${mealPlanId}`);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load shopping list");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [mealPlanId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function toggleItem(itemId: string, nextChecked: boolean) {
    if (!data) return;
    setBusyId(itemId);
    setError(null);
    try {
      await patchJson(`/shopping/items/${encodeURIComponent(itemId)}`, {
        meal_plan_id: data.meal_plan_id,
        checked: nextChecked,
      });
      setData({
        ...data,
        items: data.items.map((item) => (item.id === itemId ? { ...item, checked: nextChecked } : item)),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update checklist item");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete “${mealPlanName}” and all its meals, tracking, and shopping data? This cannot be undone.`)) {
      return;
    }
    setLoadingDelete(true);
    setError(null);
    try {
      await deleteJson<{ ok: boolean }>(`/meal-plans/${mealPlanId}`);
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete meal plan");
    } finally {
      setLoadingDelete(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white px-5 py-5 dark:border-slate-700 dark:bg-slate-900 sm:px-6 sm:py-6">
        <p className="text-sm text-slate-600 dark:text-slate-400">Loading…</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 px-5 py-5 dark:border-rose-900 dark:bg-rose-950/40 sm:px-6 sm:py-6">
        <p className="text-sm text-rose-800 dark:text-rose-200">{error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const grouped = data.items.reduce<Record<string, ShoppingItem[]>>((acc, item) => {
    const category = item.category || "other";
    if (!acc[category]) acc[category] = [];
    acc[category].push(item);
    return acc;
  }, {});

  const orderedCategories = Object.keys(grouped);
  const visibleCategories =
    categoryFilter.size === 0
      ? orderedCategories
      : orderedCategories.filter((c) => categoryFilter.has(c));

  function onCategoryChip(cat: string) {
    setCategoryFilter((prev) => {
      if (prev.size === 0) {
        return new Set([cat]);
      }
      const next = new Set(prev);
      if (next.has(cat)) {
        next.delete(cat);
      } else {
        next.add(cat);
      }
      return next;
    });
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-700 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-5">
        <button
          type="button"
          className="flex w-full flex-1 items-center justify-between gap-3 text-left"
          onClick={() => setExpanded((prev) => !prev)}
        >
          <div>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{data.meal_plan_name}</p>
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
              Meal plan #{data.meal_plan_id} · {formatDate(createdAt)}
            </p>
          </div>
          <span
            className={`shrink-0 text-slate-500 transition-transform duration-200 dark:text-slate-400 ${expanded ? "rotate-180" : "rotate-0"}`}
            aria-hidden
          >
            ▼
          </span>
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            void handleDelete();
          }}
          disabled={loadingDelete}
          className="shrink-0 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-medium text-rose-800 hover:bg-rose-100 disabled:opacity-50 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200 dark:hover:bg-rose-900/50 sm:self-center"
        >
          {loadingDelete ? "Deleting…" : "Delete list"}
        </button>
      </div>
      <div
        className={`overflow-hidden transition-all duration-200 ${
          expanded ? "max-h-[4000px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="space-y-4 px-5 pb-6 pt-2 sm:px-6 sm:pb-7 sm:pt-3">
          {error && (
            <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
              {error}
            </p>
          )}
          {orderedCategories.length > 1 && (
            <div className="flex flex-wrap gap-2 border-b border-slate-100 pb-3 dark:border-slate-700">
              <button
                type="button"
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  categoryFilter.size === 0
                    ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                    : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                }`}
                onClick={() => setCategoryFilter(new Set())}
              >
                All categories
              </button>
              {orderedCategories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${
                    categoryFilter.size > 0 && categoryFilter.has(cat)
                      ? "bg-brand-600 text-white"
                      : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                  }`}
                  onClick={() => onCategoryChip(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}
          {visibleCategories.map((category) => (
            <div key={category} className="last:mb-0">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {category}
              </p>
              <ul className="space-y-3">
                {grouped[category].map((item) => (
                  <li key={item.id}>
                    <label className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={item.checked}
                        disabled={busyId === item.id}
                        onChange={(e) => toggleItem(item.id, e.target.checked)}
                      />
                      <div
                        className={
                          item.checked
                            ? "text-sm text-slate-400 line-through dark:text-slate-500"
                            : "text-sm text-slate-900 dark:text-slate-100"
                        }
                      >
                        {item.quantity} {item.unit} {item.name}
                      </div>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ShoppingList() {
  const [plans, setPlans] = useState<MealPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPlans = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await getJson<MealPlanSummary[]>("/meal-plans");
      setPlans(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load meal plans");
      setPlans([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPlans();
  }, [loadPlans]);

  if (loading) {
    return (
      <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-300">
        Loading shopping lists…
      </p>
    );
  }

  if (error) {
    return (
      <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-950/40 dark:text-rose-200">{error}</p>
    );
  }

  if (plans.length === 0) {
    return (
      <p className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-300">
        No meal plans yet. Import a PDF on the Import tab to create a shopping list.
      </p>
    );
  }

  return (
    <section className="space-y-4">
      {plans.map((plan, index) => (
        <ShoppingListCard
          key={plan.id}
          mealPlanId={plan.id}
          mealPlanName={plan.name}
          createdAt={plan.created_at}
          defaultExpanded={index === 0}
          onDeleted={loadPlans}
        />
      ))}
    </section>
  );
}
