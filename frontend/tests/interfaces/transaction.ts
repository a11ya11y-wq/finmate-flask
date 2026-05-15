


export interface AddTransactionFormData {
    title: string;
    type: 'Income' | 'Expense';
    amount: number;
    category: string;
    date?: string; // ISO format
    note?: string;
}

export interface CreateTransactionRequest {
    title: string;
    transaction_type: 'income' | 'expense';
    amount: number;
    category_id: number;
    created_at?: string; // ISO format
    note?: string;
}