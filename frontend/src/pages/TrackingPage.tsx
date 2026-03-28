import { TrackerChecklist } from "../features/tracking/TrackerChecklist";

export function TrackingPage() {
  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-slate-900">Meal Tracker</h2>
      <p className="text-sm text-slate-600">Mark planned/eaten/skipped and attach meal photos.</p>
      <TrackerChecklist />
    </div>
  );
}
