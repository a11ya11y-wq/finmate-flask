import { useEffect, useMemo, useRef, useState } from "react";
import AppShell from "../components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import Modal from "../components/ui/modal";
import { getDashboard, getDashboardHistory } from "../api/dashboard";
import { createTransaction, deleteTransaction, updateTransaction } from "../api/transactions";
import { getCategories } from "../api/categories";
import { syncTransactions, getSyncTask } from "../api/monobank";
import type { Category, DashboardResponse, Transaction } from "../api/types";
import { toErrorMessage } from "../api/error";
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend
} from "recharts";

const COLORS = ["#3aa0ff", "#60a5fa", "#93c5fd", "#2563eb", "#1d4ed8"];
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

const formatAmount = (value: number | string | null | undefined) => {
  const numeric = toNumber(value);
  return Number.isFinite(numeric) ? numeric.toFixed(2) : "0.00";
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

const DashboardPage = () => {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [period, setPeriod] = useState<Period>("month");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isSyncOpen, setIsSyncOpen] = useState(false);
  const [editTx, setEditTx] = useState<Transaction | null>(null);
  const [deleteTx, setDeleteTx] = useState<Transaction | null>(null);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);
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
      setError(toErrorMessage(err));
    }
  };

  const loadHistory = async (selectedPeriod: Period, currentPage: number) => {
    try {
      setTableLoading(true);
      const response = await getDashboardHistory(selectedPeriod, currentPage);
      setHistory(response.data);
    } catch (err) {
      setError(toErrorMessage(err));
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
        setError(toErrorMessage(err));
      }
    };

    void loadCategories();
  }, []);

  useEffect(() => {
    if (!isSyncOpen || !taskId) {
      return;
    }

    pollRef.current = window.setInterval(async () => {
      try {
        const result = await getSyncTask(taskId);
        setSyncStatus(result.status);
        setSyncMessage(result.result?.message ?? null);
        if (result.status !== "PENDING") {
          if (pollRef.current) {
            window.clearInterval(pollRef.current);
          }
        }
      } catch (err) {
        setSyncError(toErrorMessage(err));
      }
    }, 2000);

    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
      }
    };
  }, [isSyncOpen, taskId]);

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
    setError(null);
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
      } else {
        await createTransaction(payload);
        setIsAddOpen(false);
      }
      await Promise.all([loadDashboard(period), loadHistory(period, page)]);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const confirmDelete = async () => {
    if (!deleteTx) {
      return;
    }
    setError(null);
    try {
      await deleteTransaction(deleteTx.id);
      setIsDeleteOpen(false);
      setDeleteTx(null);
      await Promise.all([loadDashboard(period), loadHistory(period, page)]);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const triggerSync = async () => {
    setSyncError(null);
    setSyncMessage(null);
    setSyncStatus("PENDING");
    try {
      const result = await syncTransactions();
      setTaskId(result.task_id);
    } catch (err) {
      setSyncError(toErrorMessage(err));
      setSyncStatus(null);
    }
  };

  const closeSyncModal = () => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
    }
    setTaskId(null);
    setSyncStatus(null);
    setSyncMessage(null);
    setSyncError(null);
    setIsSyncOpen(false);
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-300">
              <i className="bi bi-speedometer2 text-xl" />
            </span>
            <div>
              <h1 className="text-3xl font-semibold text-slate-100">Dashboard</h1>
              <p className="text-sm text-slate-400">Overview for the selected period</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 p-1">
              {periodOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={
                    period === option.value
                      ? "rounded-full bg-blue-500/20 px-4 py-2 text-xs font-semibold uppercase text-blue-200"
                      : "rounded-full px-4 py-2 text-xs font-semibold uppercase text-slate-400 hover:bg-white/5"
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
            <Button className="bg-emerald-500 text-white hover:bg-emerald-400" onClick={openAddModal}>
              + Add
            </Button>
            <Button variant="outline" onClick={() => setIsSyncOpen(true)}>
              Sync
            </Button>
          </div>
        </div>

        {loading && <p className="text-sm text-slate-400">Loading dashboard...</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}

        {data && (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="surface-card border-emerald-500/30 bg-gradient-to-br from-emerald-500/20 via-emerald-500/10 to-transparent transition hover:-translate-y-1 hover:shadow-[0_20px_60px_rgba(16,185,129,0.35)]">
                <CardHeader>
                  <CardTitle>
                    <span className="flex items-center gap-2 text-emerald-200">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/30">
                        <i className="bi bi-arrow-down" />
                      </span>
                      Total Income
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-semibold text-emerald-300">${formatAmount(data.stats.current_income)}</p>
                  <p className="text-xs text-emerald-200/80">
                    {data.stats.income_percentage_change}% vs previous period
                  </p>
                </CardContent>
              </Card>
              <Card className="surface-card border-red-500/30 bg-gradient-to-br from-red-500/20 via-red-500/10 to-transparent transition hover:-translate-y-1 hover:shadow-[0_20px_60px_rgba(239,68,68,0.35)]">
                <CardHeader>
                  <CardTitle>
                    <span className="flex items-center gap-2 text-red-200">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/30">
                        <i className="bi bi-arrow-up" />
                      </span>
                      Total Expense
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-semibold text-red-300">${formatAmount(data.stats.current_expense)}</p>
                  <p className="text-xs text-red-200/80">
                    {data.stats.expense_percentage_change}% vs previous period
                  </p>
                </CardContent>
              </Card>
              <Card className="surface-card border-blue-500/30 bg-gradient-to-br from-blue-500/20 via-blue-500/10 to-transparent transition hover:-translate-y-1 hover:shadow-[0_20px_60px_rgba(59,130,246,0.35)]">
                <CardHeader>
                  <CardTitle>
                    <span className="flex items-center gap-2 text-blue-200">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/30">
                        <i className="bi bi-wallet2" />
                      </span>
                      Current Balance
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-semibold text-blue-300">${formatAmount(data.stats.current_balance)}</p>
                  <p className="text-xs text-blue-200/80">Healthy</p>
                </CardContent>
              </Card>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <Card className="surface-card">
                <CardHeader>
                  <CardTitle>Expenses by category</CardTitle>
                </CardHeader>
                <CardContent className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={expenseChartData} dataKey="value" nameKey="name" outerRadius={110}>
                        {expenseChartData.map((_, index) => (
                          <Cell key={index} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: "#0b0f17", border: "1px solid rgba(255,255,255,0.1)" }} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card className="surface-card">
                <CardHeader>
                  <CardTitle>Balance dynamics</CardTitle>
                </CardHeader>
                <CardContent className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={balanceData}>
                      <XAxis dataKey="date" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip contentStyle={{ background: "#0b0f17", border: "1px solid rgba(255,255,255,0.1)" }} />
                      <Line type="monotone" dataKey="balance" stroke="#3aa0ff" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
            <Card className="surface-card">
              <CardHeader>
                <CardTitle>Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                {tableLoading && <p className="text-sm text-slate-400">Loading transactions...</p>}
                {!tableLoading && history.length === 0 && (
                  <p className="text-sm text-slate-400">No transactions yet.</p>
                )}
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-slate-500">
                        <th className="pb-3">Title</th>
                        <th className="pb-3">Category</th>
                        <th className="pb-3">Date</th>
                        <th className="pb-3 text-right">Amount</th>
                        <th className="pb-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {history.map((tx) => (
                        <tr key={tx.id}>
                          <td className="py-3 text-slate-100">{tx.title}</td>
                          <td className="py-3 text-slate-400">{tx.category_name}</td>
                          <td className="py-3 text-slate-400">{new Date(tx.created_at).toDateString()}</td>
                          <td className="py-3 text-right font-semibold">
                            <span className={tx.transaction_type === "income" ? "text-emerald-300" : "text-red-300"}>
                              {tx.transaction_type === "income" ? "+" : "-"}${formatAmount(tx.amount)}
                            </span>
                          </td>
                          <td className="py-3 text-right">
                            <div className="flex justify-end gap-2">
                              <Button variant="secondary" onClick={() => openEditModal(tx)}>
                                Edit
                              </Button>
                              <Button
                                variant="outline"
                                className="border-red-500/40 text-red-300 hover:bg-red-500/10"
                                onClick={() => {
                                  setDeleteTx(tx);
                                  setIsDeleteOpen(true);
                                }}
                              >
                                Delete
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
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

      <Modal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        title="Add Transaction"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitTransaction}>Save</Button>
          </div>
        }
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-slate-200">Title</label>
            <input
              className={selectStyles}
              value={form.title}
              onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Amount</label>
            <input
              type="number"
              step="0.01"
              className={selectStyles}
              value={form.amount}
              onChange={(event) => setForm((prev) => ({ ...prev, amount: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Type</label>
            <select
              className={selectStyles}
              value={form.transaction_type}
              onChange={(event) => setForm((prev) => ({ ...prev, transaction_type: event.target.value }))}
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Category</label>
            <select
              className={selectStyles}
              value={form.category_id}
              onChange={(event) => setForm((prev) => ({ ...prev, category_id: event.target.value }))}
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
            <label className="text-sm font-medium text-slate-200">Date</label>
            <input
              type="date"
              className={selectStyles}
              value={form.created_at}
              onChange={(event) => setForm((prev) => ({ ...prev, created_at: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Note</label>
            <input
              className={selectStyles}
              value={form.note}
              onChange={(event) => setForm((prev) => ({ ...prev, note: event.target.value }))}
            />
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Transaction"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitTransaction}>Save</Button>
          </div>
        }
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-slate-200">Title</label>
            <input
              className={selectStyles}
              value={form.title}
              onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Amount</label>
            <input
              type="number"
              step="0.01"
              className={selectStyles}
              value={form.amount}
              onChange={(event) => setForm((prev) => ({ ...prev, amount: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Type</label>
            <select
              className={selectStyles}
              value={form.transaction_type}
              onChange={(event) => setForm((prev) => ({ ...prev, transaction_type: event.target.value }))}
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Category</label>
            <select
              className={selectStyles}
              value={form.category_id}
              onChange={(event) => setForm((prev) => ({ ...prev, category_id: event.target.value }))}
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
            <label className="text-sm font-medium text-slate-200">Date</label>
            <input
              type="date"
              className={selectStyles}
              value={form.created_at}
              onChange={(event) => setForm((prev) => ({ ...prev, created_at: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Note</label>
            <input
              className={selectStyles}
              value={form.note}
              onChange={(event) => setForm((prev) => ({ ...prev, note: event.target.value }))}
            />
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Delete Transaction"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={confirmDelete}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-slate-300">
          Are you sure you want to delete <span className="font-semibold text-slate-100">{deleteTx?.title}</span>?
        </p>
      </Modal>

      <Modal
        isOpen={isSyncOpen}
        onClose={closeSyncModal}
        title="Monobank Sync"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={closeSyncModal}>
              Close
            </Button>
            <Button onClick={triggerSync}>Start Sync</Button>
          </div>
        }
      >
        <div className="space-y-3 text-sm text-slate-300">
          <p>Trigger manual synchronization with Monobank. The task will run asynchronously.</p>
          {syncStatus && <p>Status: <span className="text-slate-100">{syncStatus}</span></p>}
          {syncMessage && <p className="text-emerald-300">{syncMessage}</p>}
          {syncError && <p className="text-red-300">{syncError}</p>}
        </div>
      </Modal>
    </AppShell>
  );
};

export default DashboardPage;

