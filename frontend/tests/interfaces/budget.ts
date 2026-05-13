


export interface BudgetFormData {
    category: string;
    amount: number;
    isRecurring: boolean;
}

export interface CreateBudgetRequest {
    amount: number;
    category_id: number;
    is_recurring: boolean;
}