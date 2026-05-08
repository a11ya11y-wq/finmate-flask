import { test, expect } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';
import { AddTransactionFormData } from '../interfaces/transaction';


test.describe('Dashboard', () => {
    test('User can add a new transaction', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await dashboardPage.goto();
        await expect(dashboardPage.toolbar.container).toBeVisible();

        await dashboardPage.toolbar.addTransactionButton.click();
        await expect(dashboardPage.addTransactionModal.container).toBeVisible();
        
        const newTransaction: AddTransactionFormData = {
            title: 'Test Transaction',
            type: 'Expense',
            amount: 50,
            category: 'Uncategorized',
            note: 'This is a test transaction',
        }
        await dashboardPage.addTransactionModal.fillForm(newTransaction);
        await dashboardPage.addTransactionModal.submit();

        await expect(dashboardPage.addTransactionModal.container).toBeHidden();

    });
});