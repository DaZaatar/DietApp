import { ImportFlow } from "../features/meal-plans/ImportFlow";

export function ImportPage() {
  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Meal Plan Import</h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">Upload PDF, parse with AI, review JSON, then save.</p>
      <ImportFlow />
    </div>
  );
}
