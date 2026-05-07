import { useEffect, useState } from "react";
import AppShell from "../components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import Modal from "../components/ui/modal";
import { useToast } from "../components/ui/toast";
import { getBudgets, upsertBudget, deleteBudget } from "../api/budgets";
import { getCategories } from "../api/categories";
import type { BudgetWithStats, Category } from "../api/types";
import { toErrorMessage } from "../api/error";
import { ConfirmDeleteModal } from "../components/ui/ConfirmDeleteModal";


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

const getProgressColor = (percent: number) => {
  if (percent >= 100) return "bg-rose-500";
  if (percent >= 80) return "bg-amber-500";
  if (percent >= 60) return "bg-blue-400";
  return "bg-emerald-500";
};

const BudgetsPage = () => {
  const [budgets, setBudgets] = useState<BudgetWithStats[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ amount: "", category_id: "", is_recurring: true });
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const { toast } = useToast();

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
        toast({ variant: "error", message: toErrorMessage(err) });
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [toast]);

  const handleChange = (field: keyof typeof form) =>
      (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const value = field === "is_recurring" ? (event.target as HTMLInputElement).checked : event.target.value;
        setForm((prev) => ({ ...prev, [field]: value }));
      };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const isUpdate = budgets.some((b) => Number(b.category_id) === Number(form.category_id));

      await upsertBudget({
        amount: Number(form.amount),
        category_id: Number(form.category_id),
        is_recurring: form.is_recurring
      });

      // Оновлюємо дані з сервера без перезавантаження
      const freshBudgets = await getBudgets();
      setBudgets(freshBudgets);

      setForm({ amount: "", category_id: "", is_recurring: true });

      toast({
        variant: "success",
        message: isUpdate ? "Budget updated successfully!" : "Budget created successfully!"
      });
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteBudget(deleteId);
      setBudgets((prev) => prev.filter((budget) => budget.id !== deleteId));
      setIsDeleteOpen(false);
      setDeleteId(null);
      toast({ variant: "success", message: "Budget deleted successfully!" });
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  // Визначаємо, чи ми зараз оновлюємо існуючий бюджет
  const isUpdating = form.category_id
      ? budgets.some((b) => Number(b.category_id) === Number(form.category_id))
      : false;

  return (
      <AppShell>
        <div className="space-y-6">
          <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-300">
            <i className="bi bi-piggy-bank text-xl" />
          </span>
            <div>
              <h1 className="text-2xl font-bold text-white">Budgets</h1>
              <p className="text-sm text-slate-400">Track and manage your spending limits</p>
            </div>
          </div>

          {/* Шкала ліміту бюджетів */}
          <Card className="surface-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Budget limit</p>
                  <p className="text-sm font-semibold text-slate-200">{usedBudgets} / {maxBudgets} used</p>
                </div>
                <span className="text-sm font-bold text-slate-300">{progress.toFixed(0)}%</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-black/40 overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-500 ${progress >= 100 ? 'bg-rose-500' : 'bg-blue-500'}`}
                    style={{ width: `${progress}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
            {/* ФОРМА */}
            <Card className="surface-card h-fit sticky top-24">
              <CardHeader>
                <CardTitle>Create budget</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-5" onSubmit={handleSubmit}>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-300">Category</label>
                    <select
                        className={selectStyles}
                        value={form.category_id}
                        onChange={handleChange("category_id")}
                        required
                    >
                      <option value="" disabled>Select category...</option>
                      {categories.map((category) => (
                          <option key={category.id} value={category.id}>{category.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-300">Amount</label>
                    <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={form.amount}
                        onChange={handleChange("amount")}
                        required
                    />
                  </div>

                  {/* СЕКЦІЯ З ДИНАМІЧНИМ НОУТОМ */}
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/5 p-3 cursor-pointer transition-colors hover:bg-white/10">
                      <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-white/10 bg-black/50 accent-blue-500"
                          checked={form.is_recurring}
                          onChange={handleChange("is_recurring")}
                      />
                      <span className="text-sm font-medium text-slate-300">Recurring budget</span>
                    </label>

                    <div className="flex gap-2 px-1 animate-in fade-in slide-in-from-top-1 duration-300">
                      <i className={`bi ${form.is_recurring ? 'bi-info-circle' : 'bi-exclamation-circle'} text-blue-400 mt-0.5`} />
                      <p className="text-xs leading-relaxed text-slate-400">
                        {form.is_recurring
                            ? "This budget will automatically reset at the beginning of every month."
                            : "One-time: Tracks expenses only from the moment of creation until the end of the current month."}
                      </p>
                    </div>
                  </div>

                  <Button
                      type="submit"
                      variant={isUpdating ? "secondary" : "primary"}
                      className={`w-full font-bold uppercase tracking-wide ${isUpdating ? "border-blue-500/50 text-blue-300 hover:bg-blue-500/10" : ""}`}
                  >
                    {isUpdating ? (
                        <><i className="bi bi-arrow-repeat mr-2" /> Update budget</>
                    ) : (
                        <><i className="bi bi-check2 mr-2" /> Save budget</>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* СПИСОК КАРТОК БЮДЖЕТІВ */}
            <div className="grid gap-4 md:grid-cols-2 content-start">
              {!loading && budgets.length === 0 && (
                  <div className="col-span-full flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/5 py-16 text-center">
                    <i className="bi bi-piggy-bank text-6xl text-slate-600 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-300">No budgets yet</h3>
                    <p className="mt-1 text-sm text-slate-500 max-w-[250px]">Create your first budget limit to start tracking your expenses!</p>
                  </div>
              )}

              {budgets.map((budget) => {
                const rawPercent = Number(budget.percentage) || 0;
                const percent = Math.min(100, Math.max(0, rawPercent));
                const colorClass = getProgressColor(rawPercent);
                const isOverBudget = Number(budget.remaining) < 0;

                return (
                    <Card key={budget.id} className="surface-card hover:-translate-y-1 transition-all duration-300">
                      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-lg">{budget.category_name}</CardTitle>
                        <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-bold uppercase tracking-wider ${budget.is_recurring ? 'bg-blue-500/20 text-blue-300' : 'bg-slate-500/20 text-slate-300'}`}>
                      <i className={`bi ${budget.is_recurring ? 'bi-arrow-repeat' : 'bi-calendar'}`} />
                          {budget.is_recurring ? 'Recurring' : 'One-time'}
                    </span>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">Spent</span>
                          <span className="font-semibold text-slate-100">${formatAmount(budget.total_spent)}</span>
                        </div>
                        <div className="mt-3 h-2.5 rounded-full bg-black/40 overflow-hidden">
                          <div className={`h-full rounded-full transition-all duration-700 ${colorClass}`} style={{ width: `${percent}%` }} />
                        </div>
                        <div className="mt-3 flex items-center justify-between text-sm">
                          <span className="text-slate-500">{percent.toFixed(1)}% used</span>
                          <span className={`font-bold ${isOverBudget ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {isOverBudget ? 'Over budget!' : `$${formatAmount(budget.remaining)} left`}
                      </span>
                        </div>
                        <div className="mt-4 pt-4 flex items-center justify-between border-t border-white/5">
                          <div className="flex flex-col">
                            <span className="text-xs font-medium text-slate-500">Limit: ${formatAmount(budget.amount)}</span>
                            {budget.deadline_info && <span className="text-xs text-slate-600">{budget.deadline_info}</span>}
                          </div>
                          <button
                              className="flex h-8 w-8 items-center justify-center rounded-lg border border-rose-500/20 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors"
                              onClick={() => { setDeleteId(budget.id); setIsDeleteOpen(true); }}
                          >
                            <i className="bi bi-trash-fill text-sm" />
                          </button>
                        </div>
                      </CardContent>
                    </Card>
                );
              })}
            </div>
          </div>
        </div>

        <ConfirmDeleteModal
          isOpen={isDeleteOpen}
          onClose={() => setIsDeleteOpen(false)}
          onConfirm={handleDelete}
          description="Are you sure you want to delete this budget? This action cannot be undone."
        />
      </AppShell>
  );
};

export default BudgetsPage;