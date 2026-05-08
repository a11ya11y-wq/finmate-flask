import { useEffect, useMemo, useRef, useState } from "react";
import AppShell from "../components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { getDashboard, getDashboardHistory } from "../api/dashboard";
import { createTransaction, deleteTransaction, updateTransaction } from "../api/transactions";
import { getCategories } from "../api/categories";
import { syncTransactions, getSyncTask } from "../api/monobank";
import type { Category, DashboardResponse, Transaction } from "../api/types";
import { toErrorMessage } from "../api/error";
import {
  Area,
  AreaChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useToast } from "../components/ui/toast";
import { FormModal } from "../components/ui/FormModal";
import { TransactionFormFields } from "../components/ui/TransactionFormFields";
import { ConfirmDeleteModal } from "../components/ui/ConfirmDeleteModal";
// Імпортуємо наш новий хук валюти
import { useCurrency } from "../hooks/useCurrency";

const COLORS = ["#10b981", "#3b82f6", "#f43f5e", "#f59e0b", "#8b5cf6"];
const periodOptions = [
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "all", label: "All Time" }
] as const;

type Period = typeof periodOptions[number]["value"];

const selectStyles =
  "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 focus:border-blue-400/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

const toNumber = (value: number | string | null | undefined) => {
  if (value === null || value === undefined) {
    return 0;
  }
  return typeof value === "number" ? value : Number(value);
};

const toDateInput = (value?: string) => {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toISOString().slice(0, 10);
};

const formatShortDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "2-digit" });
};

const DashboardPage = () => {
  // Викликаємо хук на початку компонента
  const { formatWithSymbol } = useCurrency();

  const [activeIndex, setActiveIndex] = useState<number | undefined>(undefined);
  const [hiddenCategories, setHiddenCategories] = useState<string[]>([]);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [period, setPeriod] = useState<Period>("month");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [editTx, setEditTx] = useState<Transaction | null>(null);
  const [deleteTx, setDeleteTx] = useState<Transaction | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isSticky, setIsSticky] = useState(false);
  const pollRef = useRef<number | null>(null);
  const { toast } = useToast();
  const [form, setForm] = useState({
    title: "",
    amount: "",
    transaction_type: "expense",
    category_id: "",
    created_at: "",
    note: ""
  });

  const loadDashboard = async (selectedPeriod: Period) => {
    try {
      const response = await getDashboard(selectedPeriod);
      setData(response);
      setTotalPages(response.recent_transactions.total_page || 1);
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const loadHistory = async (selectedPeriod: Period, currentPage: number) => {
    try {
      setTableLoading(true);
      const response = await getDashboardHistory(selectedPeriod, currentPage);
      setHistory(response.data);
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadDashboard(period), loadHistory(period, page)]);
      setLoading(false);
    };

    void init();
  }, [period, page]);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await getCategories();
        setCategories(response.data);
      } catch (err) {
        toast({ variant: "error", message: toErrorMessage(err) });
      }
    };

    void loadCategories();
  }, [toast]);

  useEffect(() => {
    if (!taskId) {
      return;
    }

    pollRef.current = window.setInterval(async () => {
      try {
        const result = await getSyncTask(taskId);
        if (result.status !== "PENDING") {
          if (pollRef.current) {
            window.clearInterval(pollRef.current);
          }
          setTaskId(null);
          if (result.status === "SUCCESS") {
            toast({
              variant: "success",
              message: result.result?.message ?? "Sync completed"
            });

            void loadDashboard(period);
            void loadHistory(period, page);
          } else {
            toast({
              variant: "error",
              message: result.result?.message ?? `Sync ${result.status.toLowerCase()}`
            });
          }
        }
      } catch (err) {
        if (pollRef.current) {
          window.clearInterval(pollRef.current);
        }
        setTaskId(null);
        toast({ variant: "error", message: toErrorMessage(err) });
      }
    }, 2000);

    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
      }
    };
  }, [taskId]);

  useEffect(() => {
    const handleScroll = () => {
      setIsSticky(window.scrollY > 8);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const expenseChartData = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.charts.expenses_by_category.labels.map((label, index) => ({
      name: label,
      value: data.charts.expenses_by_category.data[index] ?? 0
    }));
  }, [data]);

  const balanceData = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.charts.balance_dynamics.labels.map((label, index) => ({
      date: label,
      balance: data.charts.balance_dynamics.data[index] ?? 0
    }));
  }, [data]);

  const resetForm = () => {
    setForm({
      title: "",
      amount: "",
      transaction_type: "expense",
      category_id: "",
      created_at: "",
      note: ""
    });
  };

  const openAddModal = () => {
    resetForm();
    setEditTx(null);
    setIsAddOpen(true);
  };

  const openEditModal = (tx: Transaction) => {
    setEditTx(tx);
    setForm({
      title: tx.title,
      amount: String(tx.amount),
      transaction_type: tx.transaction_type,
      category_id: String(tx.category_id),
      created_at: toDateInput(tx.created_at),
      note: tx.note ?? ""
    });
    setIsEditOpen(true);
  };

  const submitTransaction = async () => {
    const payload = {
      title: form.title,
      amount: Number(form.amount),
      transaction_type: form.transaction_type as "income" | "expense",
      category_id: Number(form.category_id),
      created_at: form.created_at || undefined,
      note: form.note || undefined
    };

    try {
      if (editTx) {
        await updateTransaction(editTx.id, payload);
        setIsEditOpen(false);
        // ДОДАНО: Тоаст про успішне оновлення
        toast({ variant: "success", message: "Transaction updated successfully!" });
      } else {
        await createTransaction(payload);
        setIsAddOpen(false);
        // ДОДАНО: Тоаст про успішне створення
        toast({ variant: "success", message: "Transaction added successfully!" });
      }
      await Promise.all([loadDashboard(period), loadHistory(period, page)]);
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const confirmDelete = async () => {
    if (!deleteTx) {
      return;
    }
    try {
      await deleteTransaction(deleteTx.id);
      setIsDeleteOpen(false);
      setDeleteTx(null);
      await Promise.all([loadDashboard(period), loadHistory(period, page)]);

      // ДОДАНО: Тоаст про успішне видалення
      toast({ variant: "success", message: "Transaction deleted successfully!" });
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const triggerSync = async () => {
    try {
      const result = await syncTransactions();
      setTaskId(result.task_id);
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const formatTxDate = (dateString: string) => {
    const date = new Date(dateString);
    // Формат DD.MM.YYYY
    return date.toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    });
  };

  const formatTxDay = (dateString: string) => {
    const date = new Date(dateString);
    // Назва дня тижня (напр. Mon, Tue)
    return date.toLocaleDateString("en-US", {
      weekday: "short"
    });
  };

  const getCategoryStyles = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes("food") || lower.includes("market")) {
      return { icon: "bi-cup-hot-fill", color: "text-orange-400 bg-orange-500/10" };
    }
    if (lower.includes("transport") || lower.includes("taxi") || lower.includes("car")) {
      return { icon: "bi-car-front-fill", color: "text-blue-400 bg-blue-500/10" };
    }
    if (lower.includes("health") || lower.includes("medical")) {
      return { icon: "bi-heart-pulse-fill", color: "text-rose-400 bg-rose-500/10" };
    }
    if (lower.includes("entertainment") || lower.includes("game")) {
      return { icon: "bi-controller", color: "text-purple-400 bg-purple-500/10" };
    }
    // Дефолтна іконка (Uncategorized та інше)
    return { icon: "bi-tag-fill", color: "text-slate-400 bg-slate-500/10" };
  };

  useEffect(() => {
    if (!tableLoading && history.length === 0) {
      toast({ variant: "info", message: "No transactions yet." });
    }
  }, [history.length, tableLoading, toast]);

  const unusedVariable = 123;

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="sticky top-4 z-30 mb-8 flex w-full justify-center">

          {/* Сам хедер, який динамічно змінює ширину */}
          <div data-testid="dashboard-toolbar"
              className={`flex w-full flex-col gap-4 rounded-2xl border px-6 py-4 transition-all duration-500 lg:flex-row lg:items-center lg:justify-between ${
                  isSticky
                      ? "max-w-[95%] lg:max-w-5xl border-blue-500/70 bg-[#0b0f17]/95 shadow-[0_25px_50px_-12px_rgba(0,0,0,0.7)] backdrop-blur-xl"
                      : "max-w-full border-blue-500/40 bg-[#0b0f17]/60 shadow-sm backdrop-blur-md"
              }`}
          >

            {/* Ліва частина: Іконка + Заголовок */}
            <div className="flex items-center gap-4">
              <i className="bi bi-speedometer2 text-3xl text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold tracking-wide text-white">
                  Dashboard
                </h1>
                <p className="text-sm font-medium text-slate-400">Overview for the selected period</p>
              </div>
            </div>

            {/* Права частина: Перемикачі та Кнопки */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 p-1 backdrop-blur-sm">
                {periodOptions.map((option) => (
                    <button
                        key={option.value}
                        type="button"
                        className={
                          period === option.value
                              ? "rounded-lg bg-blue-500/20 px-4 py-2 text-xs font-bold uppercase tracking-wider text-blue-200"
                              : "rounded-lg px-4 py-2 text-xs font-bold uppercase tracking-wider text-slate-400 hover:bg-white/5 transition-colors"
                        }
                        onClick={() => {
                          setPage(1);
                          setPeriod(option.value);
                        }}
                    >
                      {option.label}
                    </button>
                ))}
              </div>

              <Button
                  variant="success"
                  className="flex items-center gap-1.5 px-5 font-bold uppercase tracking-wide"
                  onClick={openAddModal}
              >
                <i className="bi bi-plus-lg" /> ADD
              </Button>

              <Button
                  variant="primary"
                  className="flex items-center gap-1.5 px-5 font-bold uppercase tracking-wide transition-all"
                  onClick={triggerSync}
                  disabled={!!taskId} // Блокуємо кнопку від повторних кліків під час процесу
              >
                <i className={`bi bi-arrow-repeat ${taskId ? "animate-spin" : ""}`} />
                {taskId ? "SYNCING..." : "SYNC"}
              </Button>
            </div>

          </div>
        </div>

         {data && (
           <>
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="surface-card border-emerald-500/40 border-t-2 bg-gradient-to-br from-[#0c1913] via-[#0a120e] to-[#0a120e] shadow-[inset_0_1px_0_rgba(16,185,129,0.35),inset_20px_20px_60px_rgba(16,185,129,0.08)] transition hover:-translate-y-1 hover:shadow-[inset_0_1px_0_rgba(16,185,129,0.45),inset_20px_20px_60px_rgba(16,185,129,0.12),0_18px_50px_rgba(16,185,129,0.25)]">
                <CardHeader>
                  <CardTitle>
                    <span className="flex items-center gap-2 text-emerald-100/80">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/30 text-emerald-100">
                        <i className="bi bi-arrow-down" />
                      </span>
                      Total Income
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* ВИКОРИСТАНО formatWithSymbol */}
                  <p className="text-3xl font-black text-emerald-500">{formatWithSymbol(data.stats.current_income)}</p>
                  <span className="mt-3 inline-flex items-center gap-2 rounded-md bg-black/40 px-2.5 py-1 text-xs font-semibold text-emerald-400">
                    <i className="bi bi-arrow-up" />
                    {data.stats.income_percentage_change}%
                  </span>
                </CardContent>
              </Card>
              <Card className="surface-card border-rose-500/40 border-t-2 bg-gradient-to-br from-[#1a0d0f] via-[#120a0a] to-[#120a0a] shadow-[inset_0_1px_0_rgba(244,63,94,0.35),inset_20px_20px_60px_rgba(244,63,94,0.08)] transition hover:-translate-y-1 hover:shadow-[inset_0_1px_0_rgba(244,63,94,0.45),inset_20px_20px_60px_rgba(244,63,94,0.12),0_18px_50px_rgba(244,63,94,0.25)]">
                <CardHeader>
                  <CardTitle>
                    <span className="flex items-center gap-2 text-rose-100/80">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-500/30 text-rose-100">
                        <i className="bi bi-arrow-up" />
                      </span>
                      Total Expense
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* ВИКОРИСТАНО formatWithSymbol */}
                  <p className="text-3xl font-black text-rose-500">{formatWithSymbol(data.stats.current_expense)}</p>
                  <span className="mt-3 inline-flex items-center gap-2 rounded-md bg-black/40 px-2.5 py-1 text-xs font-semibold text-rose-400">
                    <i className="bi bi-arrow-down" />
                    {data.stats.expense_percentage_change}%
                  </span>
                </CardContent>
              </Card>
              <Card className="surface-card border-blue-500/40 border-t-2 bg-gradient-to-br from-[#0b121a] via-[#0a0d12] to-[#0a0d12] shadow-[inset_0_1px_0_rgba(59,130,246,0.35),inset_20px_20px_60px_rgba(59,130,246,0.08)] transition hover:-translate-y-1 hover:shadow-[inset_0_1px_0_rgba(59,130,246,0.45),inset_20px_20px_60px_rgba(59,130,246,0.12),0_18px_50px_rgba(59,130,246,0.25)]">
                <CardHeader>
                  <CardTitle>
                    <span className="flex items-center gap-2 text-blue-100/80">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/30 text-blue-100">
                        <i className="bi bi-wallet2" />
                      </span>
                      Current Balance
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                    {/* Сума тепер стає червоною, якщо баланс від'ємний */}
                    {/* ВИКОРИСТАНО formatWithSymbol */}
                    <p className={`text-3xl font-black ${data.stats.current_balance < 0 ? 'text-rose-500' : 'text-blue-200'}`}>
                      {formatWithSymbol(data.stats.current_balance)}
                    </p>

                    {/* Динамічний статус-бейдж */}
                    <span className={`mt-3 inline-flex items-center gap-2 rounded-md bg-black/40 px-2.5 py-1 text-xs font-semibold ${
                      data.stats.current_balance < 0 ? 'text-rose-400' : 'text-emerald-400'
                    }`}>
                      <i className={`bi ${data.stats.current_balance < 0 ? 'bi-exclamation-triangle-fill' : 'bi-shield-check'}`} />
                      {data.stats.current_balance < 0 ? 'Overdrawn' : 'Healthy'}
                    </span>
                  </CardContent>
              </Card>
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              <Card className="surface-card transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/20 hover:shadow-[0_10px_40px_rgba(0,0,0,0.3)]">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2">
                    <i className="bi bi-pie-chart-fill text-indigo-500" />
                    Expenses by Category
                  </CardTitle>
                </CardHeader>
                {/* Збільшили загальну висоту картки до 400px */}
                <CardContent className="flex h-[400px] flex-col p-0 pb-4 relative">

                  <style>{`
      .recharts-tooltip-wrapper {
        transition: opacity 0.3s ease-in-out, transform 0.15s ease-out !important;
      }
      .smooth-pie-cell {
        transition: stroke 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        stroke: #0b0f17 !important;
        stroke-width: 2px !important;
        stroke-linejoin: round !important;
      }
      .smooth-pie-cell.is-active {
        stroke: #ffffff !important;
        opacity: 1 !important;
      }
      .smooth-pie-cell.is-dimmed {
        opacity: 0.3 !important;
      }
      
      /* --- НАШ НОВИЙ ІДЕАЛЬНИЙ СКРОЛБАР --- */
      .custom-scrollbar::-webkit-scrollbar {
        width: 4px; /* Дуже тонкий */
      }
      .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1); /* Напівпрозорий білий */
        border-radius: 10px;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2); /* Світлішає при наведенні */
      }
      /* Підтримка для Firefox */
      .custom-scrollbar {
        scrollbar-width: thin;
        scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
      }
    `}</style>

                  {(() => {
                    const activeChartData = expenseChartData
                        .filter(d => !hiddenCategories.includes(d.name))
                        .map(entry => {
                          const originalIndex = expenseChartData.findIndex(d => d.name === entry.name);
                          return {
                            ...entry,
                            fill: COLORS[originalIndex % COLORS.length]
                          };
                        });

                    const activeTotal = activeChartData.reduce((acc, curr) => acc + curr.value, 0);

                    const CustomTooltip = ({ active, payload }: any) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        const percent = activeTotal > 0 ? ((data.value / activeTotal) * 100).toFixed(1) : "0.0";

                        return (
                            <div className="z-50 animate-in fade-in duration-300 rounded-xl border border-blue-500/30 bg-[#0b0f17]/95 px-4 py-3 shadow-[0_10px_40px_rgba(0,0,0,0.6)] backdrop-blur-md">
                              <p className="mb-2 text-sm font-bold text-slate-100">{data.name}</p>
                              <div className="flex items-center gap-2">
                <span
                    className="h-3 w-3 rounded-sm"
                    style={{ backgroundColor: data.fill, boxShadow: `0 0 10px ${data.fill}80` }}
                />
                                <span className="text-sm font-medium text-emerald-400">
                  {/* ВИКОРИСТАНО formatWithSymbol */}
                  {formatWithSymbol(data.value)}
                </span>
                                <span className="text-sm font-semibold text-slate-400">
                  ({percent}%)
                </span>
                              </div>
                            </div>
                        );
                      }
                      return null;
                    };

                    return (
                        <>
                          {/* ГРАФІК: збільшено висоту блоку до 260px */}
                          <div className="h-[260px] w-full shrink-0">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                    isAnimationActive={false}
                                    data={activeChartData}
                                    dataKey="value"
                                    nameKey="name"
                                    cx="50%"
                                    cy="50%"
                                    /* Збільшили радіус, бо тепер є більше місця */
                                    innerRadius={85}
                                    outerRadius={115}
                                    onMouseEnter={(_, index) => setActiveIndex(index)}
                                    onMouseLeave={() => setActiveIndex(undefined)}
                                >
                                  {activeChartData.map((entry, index) => {
                                    const isActive = activeIndex === index;
                                    const isOtherHovered = activeIndex !== undefined && activeIndex !== index;

                                    return (
                                        <Cell
                                            key={index}
                                            fill={entry.fill}
                                            className={`smooth-pie-cell outline-none cursor-pointer ${isActive ? 'is-active' : ''} ${isOtherHovered ? 'is-dimmed' : ''}`}
                                            style={{
                                              stroke: isActive ? "#ffffff" : "#0b0f17",
                                              strokeWidth: 2,
                                              strokeLinejoin: "round",
                                              opacity: isOtherHovered ? 0.3 : 1,
                                              transition: "stroke 0.3s ease-in-out, opacity 0.3s ease-in-out"
                                            }}
                                        />
                                    );
                                  })}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} cursor={false} animationDuration={300} />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>

                          {/* ЛЕГЕНДА: автоматично заповнить залишок місця */}
                          <div className="flex-1 overflow-y-auto pl-6 pr-3 mr-4 custom-scrollbar">
                            {/* ... ТУТ ЗАЛИШАЄТЬСЯ ТВОЯ ЛЕГЕНДА БЕЗ ЗМІН ... */}
                            <ul className="mx-auto flex w-[85%] flex-col gap-3">
                              {expenseChartData.map((entry, index) => {
                                const color = COLORS[index % COLORS.length];
                                const isHidden = hiddenCategories.includes(entry.name);
                                const percent = (!isHidden && activeTotal > 0)
                                    ? ((entry.value / activeTotal) * 100).toFixed(1)
                                    : "0.0";

                                return (
                                    <li
                                        key={index}
                                        className={`group flex cursor-pointer items-center justify-between transition-all duration-300 ${isHidden ? "opacity-40 grayscale" : "opacity-100 hover:opacity-80"}`}
                                        onMouseEnter={() => {
                                          if (!isHidden) {
                                            const activeIdx = activeChartData.findIndex(d => d.name === entry.name);
                                            setActiveIndex(activeIdx !== -1 ? activeIdx : undefined);
                                          }
                                        }}
                                        onMouseLeave={() => setActiveIndex(undefined)}
                                        onClick={() => {
                                          setHiddenCategories(prev =>
                                              prev.includes(entry.name)
                                                  ? prev.filter(c => c !== entry.name)
                                                  : [...prev, entry.name]
                                          );
                                          setActiveIndex(undefined);
                                        }}
                                    >
                                      <div className="flex items-center gap-3">
                      <span
                          className="h-3 w-3 rounded-sm transition-colors duration-300 group-hover:scale-110"
                          style={{ backgroundColor: isHidden ? '#475569' : color }}
                      />
                                        <span className={`text-sm font-semibold transition-colors duration-300 ${isHidden ? 'text-slate-500 line-through' : 'text-slate-200 group-hover:text-white'}`}>
                        {entry.name}
                      </span>
                                      </div>
                                      <span className="text-sm font-semibold text-slate-400 transition-colors duration-300 group-hover:text-slate-300">
                      {percent}%
                    </span>
                                    </li>
                                );
                              })}
                            </ul>
                          </div>
                        </>
                    );
                  })()}
                </CardContent>
              </Card>
              <Card className="surface-card lg:col-span-2 transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/20 hover:shadow-[0_10px_40px_rgba(0,0,0,0.3)]">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2">
                    {/* Додали зелену іконку графіка */}
                    <i className="bi bi-graph-up-arrow text-emerald-500" />
                    Balance dynamics
                  </CardTitle>
                </CardHeader>
                {/* Задали висоту 320px, щоб ідеально збігалося з сусідньою карткою категорій */}
                <CardContent className="h-[400px] p-0 pb-4 pr-4">
                  {(() => {
                    // Наш новий стильний тултип для графіка балансу
                    const CustomBalanceTooltip = ({ active, payload, label }: any) => {
                      if (active && payload && payload.length) {
                        const data = payload[0];
                        return (
                            <div className="z-50 animate-in fade-in duration-300 rounded-xl border border-blue-500/30 bg-[#0b0f17]/95 px-4 py-3 shadow-[0_10px_40px_rgba(0,0,0,0.6)] backdrop-blur-md">
                              <p className="mb-2 text-sm font-bold text-slate-100">
                                {/* Форматуємо дату, щоб вона виглядала як Apr 23 замість 2026-04-23 */}
                                {formatShortDate(label)}
                              </p>
                              <div className="flex items-center gap-2">
                <span
                    className="h-3 w-3 rounded-sm"
                    style={{ backgroundColor: "#3b82f6", boxShadow: "0 0 10px #3b82f680" }}
                />
                                <span className="text-sm font-medium text-slate-300">
                  Balance:
                </span>
                                <span className="text-sm font-bold text-blue-400">
                  {/* ВИКОРИСТАНО formatWithSymbol */}
                  {formatWithSymbol(data.value)}
                </span>
                              </div>
                            </div>
                        );
                      }
                      return null;
                    };

                    return (
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={balanceData} margin={{ left: 0, right: 10, top: 20, bottom: 0 }}>
                            <defs>
                              <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <XAxis
                                dataKey="date"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: "#64748b", fontSize: 12 }}
                                tickFormatter={formatShortDate}
                                tickMargin={10}
                            />
                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: "#64748b", fontSize: 12 }}
                                tickMargin={10}
                            />
                            {/* Підключаємо кастомний тултип та стильну пунктирну лінію курсора */}
                            <Tooltip
                                content={<CustomBalanceTooltip />}
                                cursor={{ stroke: '#334155', strokeWidth: 1, strokeDasharray: '4 4' }}
                                animationDuration={300}
                            />
                            <Area
                                type="monotone"
                                dataKey="balance"
                                stroke="#3b82f6"
                                strokeWidth={3}
                                fill="url(#balanceGradient)"
                                dot={false}
                                activeDot={{ r: 6, fill: "#3b82f6", stroke: "#0b0f17", strokeWidth: 3 }}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                    );
                  })()}
                </CardContent>
              </Card>
            </div>
            <Card className="surface-card">
              <CardHeader>
                <CardTitle>Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mt-2 flex flex-col gap-2.5">

                  {/* НАЗВИ КОЛОНОК (Header Row) */}
                  {history.length > 0 && (
                      <div className="mb-2 hidden items-center justify-between px-4 pb-2 text-xs uppercase tracking-wider text-slate-500 md:flex border-b border-white/5">
                        {/* pl-10 (padding-left) використовуємо, щоб вирівняти слово Title після цифр нумерації */}
                        <div className="w-[35%] pl-10">Title</div>
                        <div className="w-[20%]">Category</div>
                        <div className="w-[15%] text-right">Amount</div>
                        <div className="w-[15%] text-right">Date</div>
                        <div className="w-[10%] text-right">Actions</div>
                      </div>
                  )}

                  {/* СПИСОК ТРАНЗАКЦІЙ */}
                  {history.map((tx, index) => {
                    const catStyles = getCategoryStyles(tx.category_name);
                    return (
                        <div
                            key={tx.id}
                            // Використовуємо inset тіні для ідеально рівних смужок по краях, які не ламають заокруглення
                            className="group relative flex flex-wrap items-center justify-between rounded-xl border border-white/5 bg-[#0f172a]/40 p-4 transition-all duration-300 hover:-translate-y-[1px] hover:border-blue-500/50 hover:bg-[#121a2b] hover:shadow-[inset_3px_0_0_#3b82f6,inset_-3px_0_0_#3b82f6,0_8px_20px_rgba(0,0,0,0.3)]"
                        >
                          {/* 1. Нумерація, Тайтл та Нотатка */}
                          <div className="flex w-full items-center gap-4 md:w-[35%]">
              <span className="w-6 text-center text-sm font-medium text-slate-600 transition-colors group-hover:text-blue-400">
                {index + 1}
              </span>
                            <div className="flex flex-col">
                <span className="text-base font-bold tracking-wide text-slate-100 transition-colors group-hover:text-white">
                  {tx.title}
                </span>
                              {tx.note && <span className="mt-0.5 text-xs text-slate-500">{tx.note}</span>}
                            </div>
                          </div>

                          {/* 2. Іконка та Назва категорії */}
                          <div className="mt-2 flex w-full items-center gap-2 md:mt-0 md:w-[18%]">
                            <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${catStyles.color}`}>
                              <i className={`bi ${catStyles.icon} text-xs`} />
                            </div>
                            <span className="text-xs font-semibold text-slate-300">{tx.category_name}</span>
                          </div>

                          {/* 3. Сума */}
                          <div className="flex w-1/3 justify-start md:w-[15%] md:justify-end">
              <span
                  className={`text-base font-black tracking-widest ${
                      tx.transaction_type === "income" ? "text-emerald-400" : "text-rose-500"
                  }`}
              >
                {/* ВИКОРИСТАНО formatWithSymbol */}
                {tx.transaction_type === "income" ? "+" : "-"}{formatWithSymbol(tx.amount)}
              </span>
                          </div>

                          {/* 4. Дата та День тижня */}
                          <div className="flex w-1/3 flex-col items-center md:w-[15%] md:items-end">
                            <span className="text-sm font-medium text-slate-300">{formatTxDate(tx.created_at)}</span>
                            <span className="mt-0.5 text-xs text-slate-500">{formatTxDay(tx.created_at)}</span>
                          </div>

                          {/* 5. Кнопки дій (повернуто постійні кольори) */}
                          <div className="flex w-1/3 justify-end gap-2 md:w-[10%]">
                            <button
                                className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10 text-blue-400 transition-all hover:border-blue-500/40 hover:bg-blue-500/20 hover:text-blue-300"
                                onClick={() => openEditModal(tx)}
                                title="Edit"
                            >
                              <i className="bi bi-pencil-fill text-sm" />
                            </button>
                            <button
                                className="flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/20 bg-rose-500/10 text-rose-400 transition-all hover:border-rose-500/40 hover:bg-rose-500/20 hover:text-rose-300"
                                onClick={() => {
                                  setDeleteTx(tx);
                                  setIsDeleteOpen(true);
                                }}
                                title="Delete"
                            >
                              <i className="bi bi-trash-fill text-sm" />
                            </button>
                          </div>
                        </div>
                    );
                  })}
                </div>

                {/* Пагінація (залишається як була) */}
                <div className="mt-6 flex items-center justify-between text-sm text-slate-400">
      <span>
        Page {page} of {totalPages}
      </span>
                  <div className="flex gap-2">
                    <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((prev) => prev - 1)}>
                      Prev
                    </Button>
                    <Button
                        variant="secondary"
                        disabled={page >= totalPages}
                        onClick={() => setPage((prev) => prev + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>

              </CardContent>
            </Card>
          </>
        )}
      </div>

      <FormModal
        type="add"
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onSubmit={submitTransaction}
        title="Add New Transaction"
        data-testid="add-transaction-modal"
      >
      <TransactionFormFields 
        form={form} 
        setForm={setForm} 
        categories={categories} 
        variant="success" 
      />
    </FormModal>


<FormModal
  type="edit"
  isOpen={isEditOpen}
  onClose={() => setIsEditOpen(false)}
  onSubmit={submitTransaction}
  title="Edit Transaction"
>
  <TransactionFormFields 
    form={form} 
    setForm={setForm} 
    categories={categories} 
    variant="primary" 
  />
</FormModal>

        <ConfirmDeleteModal
  isOpen={isDeleteOpen}
  onClose={() => setIsDeleteOpen(false)}
  onConfirm={confirmDelete}
  // Якщо хочеш залишити саме той текст, що був у тебе:
  description="Are you sure you want to delete this transaction?"
/>
        
    </AppShell>
  );
};

export default DashboardPage;