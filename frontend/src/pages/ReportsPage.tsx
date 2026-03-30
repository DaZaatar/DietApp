import { useMemo, useState } from "react";

import { buildApiUrl } from "../shared/lib/api";

type ReportPeriodPreset = "daily" | "weekly" | "biweekly" | "custom";
type GroupBy = "daily" | "weekly" | "biweekly";

function toInputDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function todayDateInput(): string {
  return toInputDate(new Date());
}

function minusDaysInput(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return toInputDate(d);
}

function presetRange(preset: ReportPeriodPreset): { startDate: string; endDate: string; groupBy: GroupBy } {
  switch (preset) {
    case "daily":
      return { startDate: todayDateInput(), endDate: todayDateInput(), groupBy: "daily" };
    case "weekly":
      return { startDate: minusDaysInput(6), endDate: todayDateInput(), groupBy: "weekly" };
    case "biweekly":
      return { startDate: minusDaysInput(13), endDate: todayDateInput(), groupBy: "biweekly" };
    case "custom":
    default:
      return { startDate: minusDaysInput(13), endDate: todayDateInput(), groupBy: "daily" };
  }
}

export function ReportsPage() {
  const [preset, setPreset] = useState<ReportPeriodPreset>("biweekly");
  const defaults = useMemo(() => presetRange("biweekly"), []);
  const [startDate, setStartDate] = useState(defaults.startDate);
  const [endDate, setEndDate] = useState(defaults.endDate);
  const [groupBy, setGroupBy] = useState<GroupBy>(defaults.groupBy);
  const [mealPlanId, setMealPlanId] = useState("");
  const [error, setError] = useState<string | null>(null);

  function onPresetChange(next: ReportPeriodPreset) {
    setPreset(next);
    if (next === "custom") return;
    const range = presetRange(next);
    setStartDate(range.startDate);
    setEndDate(range.endDate);
    setGroupBy(range.groupBy);
    setError(null);
  }

  function buildReportPath(autoPrint: boolean): string | null {
    if (!startDate || !endDate) {
      setError("Please set both start and end dates.");
      return null;
    }
    if (startDate > endDate) {
      setError("Start date must be on or before end date.");
      return null;
    }
    setError(null);
    const params = new URLSearchParams();
    params.set("start_date", startDate);
    params.set("end_date", endDate);
    params.set("group_by", groupBy);
    if (mealPlanId.trim()) {
      params.set("meal_plan_id", mealPlanId.trim());
    }
    if (autoPrint) {
      params.set("auto_print", "true");
    }
    return `/tracking/reports/html?${params.toString()}`;
  }

  function openReport(autoPrint: boolean) {
    const path = buildReportPath(autoPrint);
    if (!path) return;
    window.open(buildApiUrl(path), "_blank", "noopener,noreferrer");
  }

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Meal Reports</h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Generate an HTML report for planned/eaten/skipped meals by period. You can print it or save it as PDF.
      </p>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Period preset</span>
            <select
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
              value={preset}
              onChange={(e) => onPresetChange(e.target.value as ReportPeriodPreset)}
            >
              <option value="daily">Daily (today)</option>
              <option value="weekly">Weekly (last 7 days)</option>
              <option value="biweekly">Bi-weekly (last 14 days)</option>
              <option value="custom">Custom range</option>
            </select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Group by</span>
            <select
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as GroupBy)}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="biweekly">Bi-weekly</option>
            </select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Start date</span>
            <input
              type="date"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </label>

          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">End date</span>
            <input
              type="date"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </label>
        </div>

        <label className="mt-4 block text-sm">
          <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
            Optional meal plan ID filter
          </span>
          <input
            type="number"
            min={1}
            inputMode="numeric"
            placeholder="All plans"
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100 sm:max-w-xs"
            value={mealPlanId}
            onChange={(e) => setMealPlanId(e.target.value)}
          />
        </label>

        {error && (
          <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-800 dark:bg-rose-950/40 dark:text-rose-200">{error}</p>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-800 dark:border-slate-600 dark:text-slate-200"
            onClick={() => openReport(false)}
          >
            Open HTML report
          </button>
          <button
            type="button"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white dark:bg-brand-600"
            onClick={() => openReport(true)}
          >
            Open print view (save as PDF)
          </button>
        </div>
      </div>
    </section>
  );
}
