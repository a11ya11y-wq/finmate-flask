import { apiRequest } from "./client";
import type { Transaction } from "./types";

export type TransactionPayload = {
  amount: number;
  title: string;
  transaction_type: "income" | "expense";
  category_id: number;
  created_at?: string;
  note?: string;
};

export const createTransaction = async (payload: TransactionPayload) => {
  return apiRequest<Transaction>("/transactions/", {
    method: "POST",
    body: payload
  });
};

export const getTransaction = async (id: number) => {
  return apiRequest<Transaction>(`/transactions/${id}`);
};

export const updateTransaction = async (id: number, payload: Partial<TransactionPayload>) => {
  return apiRequest<Transaction>(`/transactions/${id}`, {
    method: "PUT",
    body: payload
  });
};

export const deleteTransaction = async (id: number) => {
  return apiRequest<void>(`/transactions/${id}`, {
    method: "DELETE"
  });
};

