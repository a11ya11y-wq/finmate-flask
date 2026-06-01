import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { AddTransactionFormData } from '../interfaces/transaction';
import { test, expect } from '../fixtures/dynamicUserFixture'; 
import { step } from 'allure-js-commons';

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
            
            const newTransaction: AddTransactionFormData = {
                title: `Test Transaction - ${Date.now()}`,
                type: data.type,
                amount: data.amount,
                category: data.category,
                date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
                note: data.note,
            };

            await step('Navigate to dashboard and open add transaction modal', async () => {
                await dashboardPage.goto();
                await page.waitForLoadState('networkidle');
                await dashboardPage.toolbar.addTransactionButton.click();
            });

            await step(`Fill and submit form for ${data.desc} transaction`, async () => {
                await dashboardPage.addTransactionModal.fillForm(newTransaction);
                await dashboardPage.addTransactionModal.submit();
            });

            await step('Verify success toast and modal closure', async () => {
                await dashboardPage.toast.expectSuccess('Transaction added successfully!');
                await expect(dashboardPage.addTransactionModal.modalFieldsContainer).toBeHidden();
            });

            await step('Verify the new transaction appears in the table with correct details', async () => {
                const newRow = await dashboardPage.transactionsTable.getRowByTitle(newTransaction.title);
                await expect(newRow).toBeVisible();
                await expect(newRow).toContainText('Uncategorized');
                await expect(newRow).toContainText(data.balanceAmount);
                await expect(newRow).toContainText(data.note);
            });

            await step('Verify the stats cards are updated accordingly', async () => {
                await expect(dashboardPage.currentBalanceCard.amount).toHaveText(data.balanceAmount);
                await expect(dashboardPage.currentBalanceCard.badge).toHaveText(data.balanceStatus);
                await expect(dashboardPage.totalExpenseCard.amount).toHaveText(data.totalExpenseAmount);
                await expect(dashboardPage.totalExpenseCard.badge).toHaveText(data.totalExpenseChange);
                await expect(dashboardPage.totalIncomeCard.amount).toHaveText(data.totalIncomeAmount);
                await expect(dashboardPage.totalIncomeCard.badge).toHaveText(data.totalIncomeChange);
            });
        });
    }

    test('User cannot add a transaction with empty form', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await step('Navigate to dashboard and open add transaction modal', async () => {
            await dashboardPage.goto();
            await dashboardPage.toolbar.addTransactionButton.click();
        });

        await step('Submit empty form', async () => {
            await dashboardPage.addTransactionModal.submit();
        });

        await step('Verify validation errors and modal remains open', async () => {
            await dashboardPage.expectFieldError('title', 'Enter a transaction title');
            await dashboardPage.expectFieldError('amount', 'Enter a valid amount');
            await expect(dashboardPage.addTransactionModal.modalFieldsContainer).toBeVisible();
        });
    });

    test('User can delete an existing transaction', async ({ page, api }) => {
        const dashboardPage = new DashboardPage(page);
        const uniqueTitle = `Transaction to Delete - ${Date.now()}`;

        await step('Precondition: Create a transaction to delete', async () => {
            const categoryId = await api.categories.getCategoryIdByName('Uncategorized');
            await api.transactions.createTransaction({
                title: uniqueTitle,
                transaction_type: 'expense',
                amount: 50,
                category_id: categoryId,
            });
        });

        await step('Navigate to dashboard and verify transaction exists', async () => {
            await dashboardPage.goto();
            const targetRow = await dashboardPage.transactionsTable.getRowByTitle(uniqueTitle);
            await expect(targetRow).toBeVisible();
            await expect(dashboardPage.currentBalanceCard.amount).toHaveText('-$50.00');
        });

        await step('Open delete modal and confirm deletion', async () => {
            await dashboardPage.transactionsTable.openDeleteModalFor(uniqueTitle);
            await dashboardPage.confirmDeleteModal.deleteButton.click();
        });

        await step('Verify success toast and transaction removal from table', async () => {
            await dashboardPage.toast.expectSuccess('Transaction deleted successfully!');
            const deletedRow = await dashboardPage.transactionsTable.getRowByTitle(uniqueTitle);
            await expect(deletedRow).toBeHidden();
            await expect(dashboardPage.currentBalanceCard.amount).toHaveText('$0.00');
        });
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

            await step('Precondition: Create a transaction to edit', async () => {
                const categoryId = await api.categories.getCategoryIdByName('Uncategorized');
                await api.transactions.createTransaction({
                    title: uniqueTitle,
                    transaction_type: 'expense',
                    amount: 50,
                    category_id: categoryId,
                });
            });

            await step('Navigate to dashboard and open edit modal', async () => {
                await dashboardPage.goto();
                const targetRow = await dashboardPage.transactionsTable.getRowByTitle(uniqueTitle);
                await expect(targetRow).toBeVisible();
                await expect(dashboardPage.currentBalanceCard.amount).toHaveText('-$50.00');
                await dashboardPage.transactionsTable.openEditModalFor(uniqueTitle);
            });

            await step(`Fill form with new ${data.desc} data and submit`, async () => {
                await dashboardPage.editTransactionModal.fillForm(data.newData);
                await dashboardPage.editTransactionModal.submit();
            });

            await step('Verify success toast and updated transaction details', async () => {
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
        });
    }

    test.describe('Bank sync', () => {
        test('User completes full sync flow', async ({ page }) => {
            const dashboardPage = new DashboardPage(page);
            const fakeCeleryTaskId = 'fake-task-id-12345';

            await step('Mock API responses for successful Monobank sync', async () => {
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
                            status: 'SUCCESS',
                            result: {
                                "added_count": 10,
                                "message": `Successfully synchronized 10 transaction(s)`
                            }
                        })
                    });  
                });
            });

            await step('Navigate to dashboard and initiate sync', async () => {
                await dashboardPage.goto();
                await dashboardPage.toolbar.syncTransactionButton.click();
            });

            await step('Verify success toast message', async () => {
                await dashboardPage.toast.expectSuccess('Successfully synchronized 10 transaction(s)');
            });
        });

        test('User keeps waiting while sync is started', async ({ page }) => {
            const dashboardPage = new DashboardPage(page);
            const fakeCeleryTaskId = 'fake-task-id-started';
            let pollCount = 0;

            await step('Mock API responses for started then successful Monobank sync', async () => {
                await page.route('**/api/v1/monobank/sync-transactions', async route => {
                    await route.fulfill({
                        status: 202,
                        contentType: 'application/json',
                        body: JSON.stringify({ task_id: fakeCeleryTaskId }),
                    });
                });

                await page.route(`**/api/v1/monobank/tasks/${fakeCeleryTaskId}`, async route => {
                    pollCount += 1;

                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            task_id: fakeCeleryTaskId,
                            status: pollCount === 1 ? 'STARTED' : 'SUCCESS',
                            result: pollCount === 1
                                ? null
                                : {
                                    added_count: 3,
                                    message: 'Successfully synchronized 3 transaction(s)'
                                }
                        })
                    });
                });
            });

            await step('Navigate to dashboard and initiate sync', async () => {
                await dashboardPage.goto();
                await dashboardPage.toolbar.syncTransactionButton.click();
            });

            await step('Verify success toast message after started state', async () => {
                await dashboardPage.toast.expectSuccess('Successfully synchronized 3 transaction(s)');
            });
        });

        test('User sees error toast if sync fails', async ({ page }) => {
            const dashboardPage = new DashboardPage(page);
            const fakeCeleryTaskId = 'fake-task-id-54321';

            await step('Mock API responses for failed Monobank sync', async () => {
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
                });
            });

            await step('Navigate to dashboard and initiate sync', async () => {
                await dashboardPage.goto();
                await dashboardPage.toolbar.syncTransactionButton.click();
            });

            await step('Verify error toast message', async () => {
                await dashboardPage.toast.expectError('API token not found or user access denied.');
            });
        });
    });

    test.describe('Pagination', () => {
        test('User can navigate through transaction pages', async ({ page, api }) => {
            const dashboardPage = new DashboardPage(page);

            await step('Precondition: Create 16 transactions to force pagination', async () => {
                const categoryId = await api.categories.getCategoryIdByName('Uncategorized');
                for (let i = 1; i <= 16; i++) {
                    await api.transactions.createTransaction({
                        title: `Transaction ${i}`,
                        transaction_type: 'expense',
                        amount: 50 + i,
                        category_id: categoryId,
                    });
                }
            });

            await step('Navigate to dashboard and verify first page state', async () => {
                await dashboardPage.goto();
                await expect(dashboardPage.transactionsTable.previousPageButton).toBeDisabled();
                await expect(dashboardPage.transactionsTable.paginationContainer).toHaveText(/Page 1 of 2/);
                await expect(dashboardPage.transactionsTable.rows).toHaveCount(15);
            });

            await step('Navigate to second page and verify contents', async () => {
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
});