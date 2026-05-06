import { apiRequest } from "./client";
import type { Category } from "./types";

export const getCategories = async () => {
  return apiRequest<{ data: Category[] }>("/categories/all");
};

export const createCategory = async (payload: {
  name: string;
  mcc_code?: string;
  icon: string;
}) => {
  return apiRequest<Category>("/categories/", {
    method: "POST",
    body: payload
  });
};

export const updateCategory = async (
  id: number,
  payload: { name?: string; mcc_code?: string; icon?: string }
) => {
  return apiRequest<Category>(`/categories/${id}`, {
    method: "PUT",
    body: payload
  });
};

export const deleteCategory = async (id: number) => {
  return apiRequest<void>(`/categories/${id}`, {
    method: "DELETE"
  });
};

