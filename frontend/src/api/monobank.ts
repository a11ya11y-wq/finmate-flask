import { apiRequest } from "./client";

export const syncTransactions = async () => {
  return apiRequest<{ task_id: string }>("/monobank/sync-transactions", {
    method: "POST"
  });
};

export const getSyncTask = async (taskId: string) => {
  return apiRequest<{
    task_id: string;
    status: "PENDING" | "SUCCESS" | "FAILURE";
    result: null | { added_count: number; message: string };
  }>(`/monobank/tasks/${taskId}`);
};

