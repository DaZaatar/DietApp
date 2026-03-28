import { ImportFlow } from "../features/meal-plans/ImportFlow";

export function ImportPage() {
  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-slate-900">Meal Plan Import</h2>
      <p className="text-sm text-slate-600">Upload PDF, parse with AI, review JSON, then save.</p>
      <ImportFlow />
    </div>
  );
}
