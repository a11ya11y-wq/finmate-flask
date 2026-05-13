import { test, expect } from '../fixtures/dynamicUserFixture';
import { BudgetsPage } from '../pages/BudgetsPage';


test.describe('Budgets Page', () => {
    test('User can create a new budget', async ({ page }) => {

        const budgetsPage = new BudgetsPage(page);

        await budgetsPage.goto();

        // Fill out the form
        await budgetsPage.budgetForm.fillForm({
            category: 'Food',
            amount: 500,
            isRecurring: true
        });

        await budgetsPage.budgetForm.saveButton.click();
        await budgetsPage.toast.expectSuccess('Budget created successfully');


        const newBudgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Food');
        await expect(newBudgetCard).toBeVisible();
        await expect(newBudgetCard).toContainText('$500.00 left');
        await expect(newBudgetCard).toContainText(/Recurring/i);
    });

    test('User can delete a budget', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);

        const categoryId = await api.categories.getCategoryIdByName('Food');
        await api.budgets.createBudget({
            category_id: categoryId,
            amount: 300,
            is_recurring: false
        });
        await budgetsPage.goto();
        const budgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Food');
        await expect(budgetCard).toBeVisible();
        await expect(budgetCard).toContainText('$300.00 left');

        await budgetsPage.budgetCards.deleteBudgetByCategory('Food');
        await budgetsPage.confirmDeleteModal.deleteButton.click();

        await budgetsPage.toast.expectSuccess('Budget deleted successfully!');
        await expect(budgetCard).not.toBeVisible();
    });

    test('User can edit an existing budget', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);
        const categoryId = await api.categories.getCategoryIdByName('Transport');
        await api.budgets.createBudget({
            category_id: categoryId,
            amount: 200,
            is_recurring: true
        });
        await budgetsPage.goto();
        const budgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Transport');
        await expect(budgetCard).toBeVisible();
        await expect(budgetCard).toContainText('$200.00 left');

        await budgetsPage.budgetForm.fillForm({
            category: 'Transport',
            amount: 150,
            isRecurring: false
        });
        await budgetsPage.budgetForm.updateButton.click();
        await budgetsPage.toast.expectSuccess('Budget updated successfully!');
        await expect(budgetCard).toContainText('$150.00 left');
        await expect(budgetCard).toContainText(/One-time/i);
    });

    test('Budget limit warning is displayed when total budgets exceed limit', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);
        const categoryId1 = await api.categories.getCategoryIdByName('Entertainment');
        const categoryId2 = await api.categories.getCategoryIdByName('Shopping');
        const categoryId3 = await api.categories.getCategoryIdByName('Food');
        const categoryId4 = await api.categories.getCategoryIdByName('Salary');
        const categoryId5 = await api.categories.getCategoryIdByName('Transport');
        const categories = [categoryId1, categoryId2, categoryId3, categoryId4, categoryId5];

        for (const categoryId of categories) {
            await api.budgets.createBudget({
                category_id: categoryId,
                amount: 3000,
                is_recurring: false
            });
        }
        await budgetsPage.goto();
        await expect(budgetsPage.budgetLimitContainer).toBeVisible();
        await expect(budgetsPage.budgetLimitContainer).toContainText('5 / 5 used');

        await budgetsPage.budgetForm.fillForm({
            category: 'Utilities',
            amount: 500,
            isRecurring: true
        });
        await budgetsPage.budgetForm.saveButton.click();
        await budgetsPage.toast.expectError('You have reached the limit of 5 budgets');
    });

    test('User can see correct remaining amount after creating a budget', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);
        const categoryId = await api.categories.getCategoryIdByName('Salary');
        await api.budgets.createBudget({
            category_id: categoryId,
            amount: 1000,
            is_recurring: true
        });
        await budgetsPage.goto();
        const budgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Salary');
        await expect(budgetCard).toBeVisible();
        await expect(budgetCard).toContainText('$1000.00 left');

        await api.transactions.createTransaction({
            title: 'Test Transaction',
            transaction_type: 'expense',
            amount: 200,
            category_id: categoryId,
        });
        await page.reload();
        await expect(budgetCard).toBeVisible();
        await expect(budgetCard).toContainText('$800.00 left');
    });
});