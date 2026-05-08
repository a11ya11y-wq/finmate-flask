


export interface AddTransactionFormData {
    title: string;
    type: 'Income' | 'Expense';
    amount: number;
    category: string;
    date?: string; // ISO format
    note?: string;
}