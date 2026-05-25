export type ApiError = {
  error: string;
  message?: string;
  details?: string[] | string;
};

export type User = {
  id: number;
  email: string;
  username: string;
  currency: "USD" | "EUR" | "UAH";
  monobank_token_is_set: boolean;
  avatar: string;
};

export type Category = {
  id: number;
  name: string;
  user_id: number;
  icon: string;
  mcc_code?: string | null;
};

export type Transaction = {
  id: number;
  title: string;
  amount: number;
  transaction_type: "income" | "expense";
  category_id: number;
  category_name: string;
  category_icon: string;
  created_at: string;
  note?: string | null;
  user_id: number;
};

export type Budget = {
  id: number;
  amount: number;
  category_name: string;
  category_id: number;
  created_at: string;
  is_recurring: boolean;
};

export type BudgetWithStats = Budget & {
  total_spent: number;
  percentage: number;
  remaining: number;
  deadline_info: string;
};

export type DashboardStats = {
  current_income: number;
  current_expense: number;
  current_balance: number;
  income_percentage_change: number;
  expense_percentage_change: number;
};

export type DashboardCharts = {
  expenses_by_category: {
    labels: string[];
    data: number[];
  };
  balance_dynamics: {
    labels: string[];
    data: number[];
  };
};

export type DashboardResponse = {
  stats: DashboardStats;
  charts: DashboardCharts;
  recent_transactions: {
    data: Transaction[];
    total_page: number;
  };
};

export type PaginationResponse<T> = {
  data: T[];
};

export type ReportStatus = "PENDING" | "PROCESSED" | "FAILED" | "EXPIRED";

export type ReportResponse = {
  id: number;
  status: ReportStatus;
  fileUrl?: string | null;
  error?: string | null;
};

export type ReportHistoryItem = {
  id: number;
  status: ReportStatus;
  startDate?: string | null;
  endDate?: string | null;
  createdAt?: string | null;
  expireAt?: string | null;
  fileUrl?: string | null;
};

