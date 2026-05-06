import { useEffect, useState } from "react";
import AppShell from "../components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import Modal from "../components/ui/modal";
import { getBudgets, upsertBudget, deleteBudget } from "../api/budgets";
import { getCategories } from "../api/categories";
import type { BudgetWithStats, Category } from "../api/types";
import { toErrorMessage } from "../api/error";

const selectStyles =
  "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 focus:border-blue-400/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

const toNumber = (value: number | string | null | undefined) => {
  if (value === null || value === undefined) {
    return 0;
  }
  return typeof value === "number" ? value : Number(value);
};

const formatAmount = (value: number | string | null | undefined) => {
  const numeric = toNumber(value);
  return Number.isFinite(numeric) ? numeric.toFixed(2) : "0.00";
};

const BudgetsPage = () => {
  const [budgets, setBudgets] = useState<BudgetWithStats[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ amount: "", category_id: "", is_recurring: true });
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  const maxBudgets = 5;
  const usedBudgets = budgets.length;
  const progress = Math.min(100, (usedBudgets / maxBudgets) * 100);

  useEffect(() => {
    const load = async () => {
      try {
        const [budgetsResponse, categoriesResponse] = await Promise.all([
          getBudgets(),
          getCategories()
        ]);
        setBudgets(budgetsResponse);
        setCategories(categoriesResponse.data);
      } catch (err) {
        setError(toErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const handleChange = (field: keyof typeof form) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const value = field === "is_recurring" ? (event.target as HTMLInputElement).checked : event.target.value;
      setForm((prev) => ({ ...prev, [field]: value }));
    };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      const result = await upsertBudget({
        amount: form.amount,
        category_id: Number(form.category_id),
        is_recurring: form.is_recurring
      });
      setBudgets((prev) => {
        const existing = prev.find((budget) => budget.id === result.id);
        if (existing) {
          return prev.map((budget) => (budget.id === result.id ? result : budget));
        }
        return [result, ...prev];
      });
      setForm({ amount: "", category_id: "", is_recurring: true });
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handleDelete = async () => {
    if (!deleteId) {
      return;
    }
    setError(null);
    try {
      await deleteBudget(deleteId);
      setBudgets((prev) => prev.filter((budget) => budget.id !== deleteId));
      setIsDeleteOpen(false);
      setDeleteId(null);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-300">
            <i className="bi bi-piggy-bank text-xl" />
          </span>
          <div>
            <h1 className="text-3xl font-semibold text-slate-100">Budgets</h1>
            <p className="text-sm text-slate-400">Track and manage your spending limits</p>
          </div>
        </div>

        <Card className="surface-card">
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Budget limit</p>
                <p className="text-sm text-slate-200">
                  {usedBudgets} / {maxBudgets} used
                </p>
              </div>
              <span className="text-sm text-slate-400">{progress.toFixed(0)}%</span>
            </div>
            <div className="mt-3 h-2 rounded-full bg-white/5">
              <div className="h-2 rounded-full bg-blue-500" style={{ width: `${progress}%` }} />
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <Card className="surface-card">
            <CardHeader>
              <CardTitle>Create budget</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label className="text-sm font-medium text-slate-200">Category</label>
                  <select
                    className={selectStyles}
                    value={form.category_id}
                    onChange={handleChange("category_id")}
                    required
                  >
                    <option value="" disabled>
                      Select category
                    </option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-200">Amount</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.amount}
                    onChange={handleChange("amount")}
                    required
                  />
                </div>
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-blue-500"
                    checked={form.is_recurring}
                    onChange={handleChange("is_recurring")}
                  />
                  Recurring budget
                </label>
                {error && <p className="text-sm text-red-400">{error}</p>}
                <Button type="submit" className="w-full">
                  Save budget
                </Button>
              </form>
            </CardContent>
          </Card>
          <div className="grid gap-4 md:grid-cols-2">
            {loading && <p className="text-sm text-slate-400">Loading budgets...</p>}
            {!loading && budgets.length === 0 && (
              <p className="text-sm text-slate-400">No budgets created yet.</p>
            )}
            {budgets.map((budget) => {
              const percent = Math.min(100, Math.max(0, budget.percentage));
              return (
                <Card key={budget.id} className="surface-card">
                  <CardHeader>
                    <CardTitle>{budget.category_name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm text-slate-400">
                      <span>${formatAmount(budget.total_spent)} spent</span>
                      <span>${formatAmount(budget.amount)} limit</span>
                    </div>
                    <div className="mt-3 h-2 rounded-full bg-white/5">
                      <div
                        className="h-2 rounded-full bg-emerald-500"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                      <span>{budget.deadline_info}</span>
                      <span>${formatAmount(budget.remaining)} remaining</span>
                    </div>
                    <Button
                      variant="outline"
                      className="mt-4 border-red-500/40 text-red-300 hover:bg-red-500/10"
                      onClick={() => {
                        setDeleteId(budget.id);
                        setIsDeleteOpen(true);
                      }}
                    >
                      Remove
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>

      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Delete budget"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-slate-300">Are you sure you want to delete this budget?</p>
      </Modal>
    </AppShell>
  );
};

export default BudgetsPage;

