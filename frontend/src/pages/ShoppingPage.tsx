import { ShoppingList } from "../features/shopping/ShoppingList";

export function ShoppingPage() {
  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-slate-900">Shopping List</h2>
      <p className="text-sm text-slate-600">
        One expandable checklist per imported meal plan (newest first). Checkboxes are saved per user.
      </p>
      <ShoppingList />
    </div>
  );
}
