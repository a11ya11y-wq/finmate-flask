import { apiRequest } from "./client";
import type { DashboardResponse, PaginationResponse, Transaction } from "./types";

export const getDashboard = async (period: "all" | "week" | "month" = "all") => {
  return apiRequest<DashboardResponse>(`/dashboard/?period=${period}`);
};

export const getDashboardHistory = async (
  period: "all" | "week" | "month" = "all",
  page = 1
) => {
  return apiRequest<PaginationResponse<Transaction>>(
    `/dashboard/history?period=${period}&page=${page}`
  );
};

