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
import { budgetSchema } from "../validation/schemas";
import { validateForm } from "../validation/validate";
import { cn } from "../lib/utils";
// Імпортуємо наш новий хук валюти
import { useCurrency } from "../hooks/useCurrency";

const selectStyles =
    "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 focus:border-blue-400/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

const getProgressColor = (percent: number) => {
  if (percent >= 100) return "bg-rose-500";
  if (percent >= 80) return "bg-amber-500";
  if (percent >= 60) return "bg-blue-400";
  return "bg-emerald-500";
};

const BudgetsPage = () => {
  // Викликаємо хук на початку компонента
  const { currencySymbol, formatWithSymbol } = useCurrency();

  const [budgets, setBudgets] = useState<BudgetWithStats[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ amount: "", category_id: "", is_recurring: true });
  const [errors, setErrors] = useState<Record<string, string>>({});
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
        if (field === "category_id") {
          const selectedBudget = budgets.find((budget) => String(budget.category_id) === String(value));
          setForm((prev) => ({
            ...prev,
            category_id: String(value),
            amount: selectedBudget ? String(selectedBudget.amount) : "",
            is_recurring: selectedBudget ? selectedBudget.is_recurring : true
          }));
          setErrors((prev) => {
            if (!prev.category_id && !prev.amount) {
              return prev;
            }
            const next = { ...prev };
            delete next.category_id;
            delete next.amount;
            return next;
          });
          return;
        }

        setForm((prev) => ({ ...prev, [field]: value }));
        setErrors((prev) => {
          if (!prev[field]) {
            return prev;
          }
          const next = { ...prev };
          delete next[field];
          return next;
        });
      };

  const normalizeBudgetCompare = (value: { amount: number; is_recurring: boolean }) => {
    return {
      amount: Math.round(value.amount * 100) / 100,
      is_recurring: value.is_recurring
    };
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const validation = validateForm(budgetSchema, form);
    if (!validation.success) {
      setErrors(validation.fieldErrors ?? {});
      return;
    }
    try {
      setErrors({});
      const selectedBudget = budgets.find((b) => Number(b.category_id) === Number(form.category_id));
      const isUpdate = !!selectedBudget;
      if (selectedBudget) {
        const currentComparable = normalizeBudgetCompare({
          amount: validation.data.amount,
          is_recurring: validation.data.is_recurring
        });
        const snapshotComparable = normalizeBudgetCompare({
          amount: Number(selectedBudget.amount),
          is_recurring: selectedBudget.is_recurring
        });
        const isDirty = Object.keys(snapshotComparable).some((key) => {
          return snapshotComparable[key as keyof typeof snapshotComparable] !== currentComparable[key as keyof typeof currentComparable];
        });
        if (!isDirty) {
          return;
        }
      }

      await upsertBudget({
        amount: validation.data.amount,
        category_id: Number(validation.data.category_id),
        is_recurring: validation.data.is_recurring
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
            <CardContent data-testid="budgets-limit-container" className="pt-6">
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
            <Card data-testid="budgets-form-container" className="surface-card h-fit sticky top-24">
              <CardHeader>
                <CardTitle>Create budget</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-5" onSubmit={handleSubmit} noValidate>
                  <div className="space-y-1.5">
                    <label htmlFor="category-label" className="text-sm font-medium text-slate-300">Category</label>
                    <select
                        id="category-label"
                        className={cn(
                          selectStyles,
                          errors.category_id && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
                        )}
                        value={form.category_id}
                        onChange={handleChange("category_id")}
                        required
                      aria-invalid={!!errors.category_id}
                    >
                      <option value="" disabled>Select category...</option>
                      {categories.map((category) => (
                          <option key={category.id} value={category.id}>{category.name}</option>
                      ))}
                    </select>
                    {errors.category_id && <p className="text-xs text-rose-400">{errors.category_id}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="amount-input" className="text-sm font-medium text-slate-300">Amount</label>
                    <div className="relative">
                      {/* ВИКОРИСТАНО currencySymbol */}
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">{currencySymbol}</span>
                      <Input
                          id="amount-input"
                          type="number"
                          step="0.01"
                          className={cn(
                            "pl-7",
                            errors.amount && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
                          )}
                          placeholder="0.00"
                          value={form.amount}
                          onChange={handleChange("amount")}
                          required
                          aria-invalid={!!errors.amount}
                      />
                    </div>
                    {errors.amount && <p className="text-xs text-rose-400">{errors.amount}</p>}
                  </div>

                  {/* СЕКЦІЯ З ДИНАМІЧНИМ НОУТОМ */}
                  <div className="space-y-3">
                    <label htmlFor="recurring-checkbox" className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/5 p-3 cursor-pointer transition-colors hover:bg-white/10">
                      <input
                          id="recurring-checkbox"
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
                    <Card
                      key={budget.id}
                      data-testid="budget-card"
                      className="surface-card hover:-translate-y-1 transition-all duration-300"
                    >
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
                          {/* ВИКОРИСТАНО formatWithSymbol */}
                          <span className="font-semibold text-slate-100">{formatWithSymbol(budget.total_spent)}</span>
                        </div>
                        <div className="mt-3 h-2.5 rounded-full bg-black/40 overflow-hidden">
                          <div className={`h-full rounded-full transition-all duration-700 ${colorClass}`} style={{ width: `${percent}%` }} />
                        </div>
                        <div className="mt-3 flex items-center justify-between text-sm">
                          <span className="text-slate-500">{percent.toFixed(1)}% used</span>
                          <span className={`font-bold ${isOverBudget ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {/* ВИКОРИСТАНО formatWithSymbol */}
                        {isOverBudget ? 'Over budget!' : `${formatWithSymbol(budget.remaining)} left`}
                      </span>
                        </div>
                        <div className="mt-4 pt-4 flex items-center justify-between border-t border-white/5">
                          <div className="flex flex-col">
                            {/* ВИКОРИСТАНО formatWithSymbol */}
                            <span className="text-xs font-medium text-slate-500">Limit: {formatWithSymbol(budget.amount)}</span>
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