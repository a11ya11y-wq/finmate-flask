import { DashboardPage } from '../pages/DashboardPage';
import { AddTransactionFormData } from '../interfaces/transaction';
import { test, expect } from '../fixtures/dynamicUserFixture'; 



test.describe('Dashboard Actions', () => {

    test('User can add a new transaction', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        await dashboardPage.goto();

        await dashboardPage.toolbar.addTransactionButton.click();
        
        const newTransaction: AddTransactionFormData = {
            title: 'Test Transaction - ' + Date.now(),
            type: 'Expense',
            amount: 50,
            category: 'Uncategorized',
            note: 'This is a test transaction',
        }
        await dashboardPage.addTransactionModal.fillForm(newTransaction);
        await dashboardPage.addTransactionModal.submit();

        await dashboardPage.toast.expectSuccess('Transaction added successfully!');

        await expect(dashboardPage.addTransactionModal.container).toBeHidden();

        const newRow = await dashboardPage.transactionsTable.getRowByTitle(newTransaction.title);
        await expect(newRow).toBeVisible();
        await expect(newRow).toContainText('Uncategorized');
    });

    test('User can delete an existing transaction', async ({ page, api }) => {
        const dashboardPage = new DashboardPage(page);

        const uniqueTitle = 'Transaction to Delete - ' + Date.now();
        const categoryId = await api.categories.getCategoryIdByName('Uncategorized');
        await api.transactions.createTransaction({
            title: uniqueTitle,
            transaction_type: 'expense',
            amount: 50,
            category_id: categoryId,
        });


        await dashboardPage.goto();
        await dashboardPage.transactionsTable.openDeleteModalFor(uniqueTitle);
        await dashboardPage.confirmDeleteModal.deleteButton.click();

        await dashboardPage.toast.expectSuccess('Transaction deleted successfully!');

        const deletedRow = await dashboardPage.transactionsTable.getRowByTitle(uniqueTitle);
        await expect(deletedRow).toBeHidden();

    });
});