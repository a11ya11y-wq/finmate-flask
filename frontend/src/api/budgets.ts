import { apiRequest } from "./client";
import type { BudgetWithStats } from "./types";

export const getBudgets = async () => {
  return apiRequest<BudgetWithStats[]>("/budgets/");
};

export const upsertBudget = async (payload: {
  amount: string | number;
  category_id: number;
  is_recurring: boolean;
}) => {
  return apiRequest<BudgetWithStats>("/budgets/", {
    method: "POST",
    body: payload
  });
};

export const deleteBudget = async (id: number) => {
  return apiRequest<void>(`/budgets/${id}`, {
    method: "DELETE"
  });
};

