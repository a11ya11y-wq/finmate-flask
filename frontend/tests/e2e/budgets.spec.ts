import { Locator } from '@playwright/test';
import { test, expect } from '../fixtures/dynamicUserFixture';
import { BudgetsPage } from '../pages/budgets/BudgetsPage';
import { step } from 'allure-js-commons';

test.describe('Budgets Page', () => {
    test('User can create a new budget', async ({ page }) => {
        const budgetsPage = new BudgetsPage(page);
        let newBudgetCard: Locator;

        await step('Navigate to the budgets page', async () => {
            await budgetsPage.goto();
        });

        await step('Fill out and submit the new budget form', async () => {
            await budgetsPage.budgetForm.fillForm({
                category: 'Food',
                amount: 500,
                isRecurring: true
            });
            await budgetsPage.budgetForm.saveButton.click();
        });

        await step('Verify success message and new budget card details', async () => {
            await budgetsPage.toast.expectSuccess('Budget created successfully');
            
            newBudgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Food');
            await expect(newBudgetCard).toBeVisible();
            await expect(newBudgetCard).toContainText('$500.00 left');
            await expect(newBudgetCard).toContainText(/Recurring/i);
        });
    });

    test('User can delete a budget', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);
        let budgetCard: Locator;

        await step('Precondition: Create a budget via API', async () => {
            const categoryId = await api.categories.getCategoryIdByName('Food');
            await api.budgets.createBudget({
                category_id: categoryId,
                amount: 300,
                is_recurring: false
            });
        });

        await step('Navigate to budgets page and verify budget exists', async () => {
            await budgetsPage.goto();
            budgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Food');
            await expect(budgetCard).toBeVisible();
            await expect(budgetCard).toContainText('$300.00 left');
        });

        await step('Initiate budget deletion and confirm', async () => {
            await budgetsPage.budgetCards.deleteBudgetByCategory('Food');
            await budgetsPage.confirmDeleteModal.deleteButton.click();
        });

        await step('Verify success message and budget removal from UI', async () => {
            await budgetsPage.toast.expectSuccess('Budget deleted successfully!');
            await expect(budgetCard).not.toBeVisible();
        });
    });

    test('User can edit an existing budget', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);
        let budgetCard: Locator;

        await step('Precondition: Create a budget via API', async () => {
            const categoryId = await api.categories.getCategoryIdByName('Transport');
            await api.budgets.createBudget({
                category_id: categoryId,
                amount: 200,
                is_recurring: true
            });
        });

        await step('Navigate to budgets page and verify initial budget state', async () => {
            await budgetsPage.goto();
            budgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Transport');
            await expect(budgetCard).toBeVisible();
            await expect(budgetCard).toContainText('$200.00 left');
        });

        await step('Update budget details via the edit form', async () => {
            await budgetsPage.budgetForm.fillForm({
                category: 'Transport',
                amount: 150,
                isRecurring: false
            });
            await budgetsPage.budgetForm.updateButton.click();
        });

        await step('Verify success message and updated budget details', async () => {
            await budgetsPage.toast.expectSuccess('Budget updated successfully!');
            await expect(budgetCard).toContainText('$150.00 left');
            await expect(budgetCard).toContainText(/One-time/i);
        });
    });

    test('Budget limit warning is displayed when total budgets exceed limit', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);

        await step('Precondition: Create 5 budgets via API to reach the limit', async () => {
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
        });

        await step('Navigate to budgets page and verify limit warning container', async () => {
            await budgetsPage.goto();
            await page.waitForLoadState('networkidle');
            
            await expect(budgetsPage.budgetLimitContainer).toBeVisible();
            await expect(budgetsPage.budgetLimitContainer).toContainText('5 / 5 used');
        });

        await step('Attempt to create a 6th budget via UI', async () => {
            await budgetsPage.budgetForm.fillForm({
                category: 'Utilities',
                amount: 500,
                isRecurring: true
            });
            await budgetsPage.budgetForm.saveButton.click();
        });

        await step('Verify budget limit error toast', async () => {
            await budgetsPage.toast.expectError('You have reached the limit of 5 budgets');
        });
    });

    test('User can see correct remaining amount after creating a budget', async ({ page, api }) => {
        const budgetsPage = new BudgetsPage(page);
        let budgetCard: Locator;
        let categoryId: number;

        await step('Precondition: Create a budget via API', async () => {
            categoryId = await api.categories.getCategoryIdByName('Salary');
            await api.budgets.createBudget({
                category_id: categoryId,
                amount: 1000,
                is_recurring: true
            });
        });

        await step('Navigate to budgets page and verify initial remaining amount', async () => {
            await budgetsPage.goto();
            budgetCard = await budgetsPage.budgetCards.getBudgetCardByCategory('Salary');
            await expect(budgetCard).toBeVisible();
            await expect(budgetCard).toContainText('$1000.00 left');
        });

        await step('Create an expense transaction and reload page', async () => {
            await api.transactions.createTransaction({
                title: 'Test Transaction',
                transaction_type: 'expense',
                amount: 200,
                category_id: categoryId,
            });
            await budgetsPage.goto();
        });

        await step('Verify remaining amount is reduced by the transaction amount', async () => {
            await expect(budgetCard).toBeVisible();
            await expect(budgetCard).toContainText('$800.00 left');
        });
    });
});