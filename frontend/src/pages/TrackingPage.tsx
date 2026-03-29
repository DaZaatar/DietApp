import { TrackerChecklist } from "../features/tracking/TrackerChecklist";

export function TrackingPage() {
  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Meal Tracker</h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">Mark planned/eaten/skipped and attach meal photos.</p>
      <TrackerChecklist />
    </div>
  );
}
