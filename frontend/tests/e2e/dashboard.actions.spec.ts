import { DashboardPage } from '../pages/DashboardPage';
import { AddTransactionFormData } from '../interfaces/transaction';
import { test, expect } from '../fixtures/dynamicUserFixture'; 



test.describe('Dashboard Actions', () => {
    const createTransactionData = [
        {
            desc: 'Income', type: 'Income' as const, amount: 100, category: 'Uncategorized', 
            note: 'Test income transaction', balanceAmount: '$100.00', balanceStatus: 'Healthy', totalIncomeAmount: '$100.00', totalIncomeChange: '100%', 
            totalExpenseAmount: '$0.00', totalExpenseChange: '0%', 
        },
        {
            desc: 'Expense', type: 'Expense' as const, amount: 50, category: 'Uncategorized', note: 'Test expense transaction',
            balanceAmount: '-$50.00', balanceStatus: 'Overdrawn', totalIncomeAmount: '$0.00', totalIncomeChange: '0%',
            totalExpenseAmount: '$50.00', totalExpenseChange: '100%',
        }
    ];
    for (const data of createTransactionData) {
        test(`User can add a new ${data.desc} transaction`, async ({ page }) => {
            const dashboardPage = new DashboardPage(page);
            await dashboardPage.goto();

            await dashboardPage.toolbar.addTransactionButton.click();
            
            const newTransaction: AddTransactionFormData = {
                title: `Test Transaction - ${Date.now()}`,
                type: data.type,
                amount: data.amount,
                category: data.category,
                date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
                note: data.note,
            }
            await dashboardPage.addTransactionModal.fillForm(newTransaction);
            await dashboardPage.addTransactionModal.submit();
            await dashboardPage.toast.expectSuccess('Transaction added successfully!');

            await expect(dashboardPage.addTransactionModal.modalFieldsContainer).toBeHidden();

            const newRow = await dashboardPage.transactionsTable.getRowByTitle(newTransaction.title);
            // Verify the new transaction appears in the table with correct details
            await expect(newRow).toBeVisible();
            await expect(newRow).toContainText('Uncategorized');
            await expect(newRow).toContainText(data.balanceAmount);
            await expect(newRow).toContainText(data.note);
            // Verify the stats cards are updated
            await expect(dashboardPage.currentBalanceCard.amount).toHaveText(data.balanceAmount);
            await expect(dashboardPage.currentBalanceCard.badge).toHaveText(data.balanceStatus);
            await expect(dashboardPage.totalExpenseCard.amount).toHaveText(data.totalExpenseAmount);
            await expect(dashboardPage.totalExpenseCard.badge).toHaveText(data.totalExpenseChange);
            await expect(dashboardPage.totalIncomeCard.amount).toHaveText(data.totalIncomeAmount);
            await expect(dashboardPage.totalIncomeCard.badge).toHaveText(data.totalIncomeChange);
        });
    }
    test('User cannot add a transaction with empty form', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        await dashboardPage.goto();

        await dashboardPage.toolbar.addTransactionButton.click();
        await dashboardPage.addTransactionModal.submit();

        await dashboardPage.toast.expectError('Input should be greater than 0');
        await expect(dashboardPage.addTransactionModal.modalFieldsContainer).toBeVisible();
    });

    test('User can delete an existing transaction', async ({ page, api }) => {
        const dashboardPage = new DashboardPage(page);

        const uniqueTitle = `Transaction to Delete - ${Date.now()}`;
        const categoryId = await api.categories.getCategoryIdByName('Uncategorized');
        await api.transactions.createTransaction({
            title: uniqueTitle,
            transaction_type: 'expense',
            amount: 50,
            category_id: categoryId,
        });


        await dashboardPage.goto();

        const targetRow = await dashboardPage.transactionsTable.getRowByTitle(uniqueTitle);
        await expect(targetRow).toBeVisible();
        await expect(dashboardPage.currentBalanceCard.amount).toHaveText('-$50.00');

        await dashboardPage.transactionsTable.openDeleteModalFor(uniqueTitle);
        await dashboardPage.confirmDeleteModal.deleteButton.click();

        await dashboardPage.toast.expectSuccess('Transaction deleted successfully!');

        const deletedRow = await dashboardPage.transactionsTable.getRowByTitle(uniqueTitle);
        await expect(deletedRow).toBeHidden();
        await expect(dashboardPage.currentBalanceCard.amount).toHaveText('$0.00');

    });
    const editTransactionData: { desc: string; newData: Partial<AddTransactionFormData> }[] = [
        {
            desc: 'all fields', newData: {
            title: `Edited Transaction - ${Date.now()}`,
            type: 'Income',
            amount: 150,
            category: 'Food',
            note: 'Edited transaction note'
        }
    },
    {
            desc: 'amount and type', newData: {
                type: 'Income',
                amount: 200,
            }
        },
        {
            desc: 'category and note', newData: {
                category: 'Transport',
                note: 'Edited category and note'
            }
        }
    ];
    for (const data of editTransactionData) {
        test(`User can edit ${data.desc} of a transaction`, async ({ page, api }) => {
            const dashboardPage = new DashboardPage(page);

            const uniqueTitle = `Transaction to Edit - ${Date.now()}`;
            const categoryId = await api.categories.getCategoryIdByName('Uncategorized');
            await api.transactions.createTransaction({
                title: uniqueTitle,
                transaction_type: 'expense',
                amount: 50,
                category_id: categoryId,
            });

            await dashboardPage.goto();

            const targetRow = await dashboardPage.transactionsTable.getRowByTitle(uniqueTitle);
            await expect(targetRow).toBeVisible();
            await expect(dashboardPage.currentBalanceCard.amount).toHaveText('-$50.00');

            await dashboardPage.transactionsTable.openEditModalFor(uniqueTitle);

            await dashboardPage.editTransactionModal.fillForm(data.newData);
            await dashboardPage.editTransactionModal.submit();

            await dashboardPage.toast.expectSuccess('Transaction updated successfully!');

            const expectedTitle = data.newData.title || uniqueTitle;
            const editedRow = await dashboardPage.transactionsTable.getRowByTitle(expectedTitle);
            await expect(editedRow).toBeVisible();

            if (data.newData.type) {
                const expectedAmount = data.newData.type === 'Income' ? `$${data.newData.amount!.toFixed(2)}` : `-$${data.newData.amount!.toFixed(2)}`;
                await expect(editedRow).toContainText(expectedAmount);
                await expect(dashboardPage.currentBalanceCard.amount).toHaveText(expectedAmount);
            }
            if (data.newData.category) {
                await expect(editedRow).toContainText(data.newData.category);
            }
            if (data.newData.note) {
                await expect(editedRow).toContainText(data.newData.note);
            }
            if (data.newData.title) {
                await expect(editedRow).toContainText(data.newData.title);
            }

        });
    }
    test.describe('Bank sync', () => {
        test('User completes full sync flow', async ({ page }) => {
            const dashboardPage = new DashboardPage(page);

            // Mock the API response for initiating sync
            const fakeCeleryTaskId = 'fake-task-id-12345';
            await page.route('**/api/v1/monobank/sync-transactions', async route => {
                await route.fulfill({
                    status: 202,
                    contentType: 'application/json',
                    body: JSON.stringify({ task_id: fakeCeleryTaskId }),
                });
            });

            await page.route(`**/api/v1/monobank/tasks/${fakeCeleryTaskId}`, async route => {
                await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    task_id: fakeCeleryTaskId,
                    status: 'SUCCESS', // if 0 new tx == SUCCESS but with 0 count
                    result: {
                        "added_count": 10, // Service returns number of transactions synced
                        "message": `Successfully synchronized 10 transaction(s)`
                    }
                })
            });  
        });
        await dashboardPage.goto();
        await dashboardPage.toolbar.syncTransactionButton.click();
        await dashboardPage.toast.expectSuccess('Successfully synchronized 10 transaction(s)');
        });
    test('User sees error toast if sync fails', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);

        // Mock the API response for initiating sync
        const fakeCeleryTaskId = 'fake-task-id-54321';
        await page.route('**/api/v1/monobank/sync-transactions', async route => {
            await route.fulfill({
                status: 202,
                contentType: 'application/json',
                body: JSON.stringify({ task_id: fakeCeleryTaskId }),
            });
        });

        await page.route(`**/api/v1/monobank/tasks/${fakeCeleryTaskId}`, async route => {
            await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                task_id: fakeCeleryTaskId,
                status: 'FAILURE',
                result: {
                    "added_count": 0,
                    "message": 'API token not found or user access denied.'
                }
            })
        });
        await dashboardPage.goto();
        await dashboardPage.toolbar.syncTransactionButton.click();
        await dashboardPage.toast.expectError('API token not found or user access denied.');

        });
    });
    });

    test.describe('Pagination', () => {
        test('User can navigate through transaction pages', async ({ page, api }) => {
            const dashboardPage = new DashboardPage(page);

            const categoryId = await api.categories.getCategoryIdByName('Uncategorized');
            for (let i = 1; i <= 16; i++) {
                await api.transactions.createTransaction({
                    title: `Transaction ${i}`,
                    transaction_type: 'expense',
                    amount: 50 + i,
                    category_id: categoryId,
                });
            }
            await dashboardPage.goto();
            await expect(dashboardPage.transactionsTable.previousPageButton).toBeDisabled();
            await expect(dashboardPage.transactionsTable.paginationContainer).toHaveText(/Page 1 of 2/);
            await expect(dashboardPage.transactionsTable.rows).toHaveCount(15);

            await dashboardPage.transactionsTable.nextPageButton.click();
            await expect(dashboardPage.transactionsTable.paginationContainer).toHaveText(/Page 2 of 2/);
            await expect(dashboardPage.transactionsTable.rows).toHaveCount(1);
            const page2Row = await dashboardPage.transactionsTable.getRowByTitle('Transaction 1');
            await expect(page2Row).toBeVisible();
            await expect(page2Row).toContainText('-$51.00');

            await expect(dashboardPage.transactionsTable.previousPageButton).toBeEnabled();
            await expect(dashboardPage.transactionsTable.nextPageButton).toBeDisabled();
        });
    });
});