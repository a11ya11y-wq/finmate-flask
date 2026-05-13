import { test, expect } from '../fixtures/dynamicUserFixture'; 
import { DashboardPage } from '../pages/DashboardPage';



test.describe('Dashboard View', () => {
    test('Dashboard should display correct initial state for new user', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        await dashboardPage.goto();

        await expect(page).toHaveURL(/.*\/dashboard/);
        await dashboardPage.toast.expectInfo('No transactions yet.');

        // Header
        await expect(dashboardPage.header.container).toBeVisible();
        await expect(dashboardPage.header.logo).toBeVisible();
        await expect(dashboardPage.header.userMenuToggle).toBeVisible();
        await expect(dashboardPage.header.userAvatar).toBeVisible();

        // Toolbar
        await expect(dashboardPage.toolbar.title).toHaveText('Dashboard');
        await expect(dashboardPage.toolbar.periodFilterContainer).toBeVisible();
        await expect(dashboardPage.toolbar.filterWeek).toBeVisible();
        await expect(dashboardPage.toolbar.filterMonth).toBeVisible();
        await expect(dashboardPage.toolbar.filterAllTime).toBeVisible();
        
        await expect(dashboardPage.toolbar.addTransactionButton).toBeVisible();
        await expect(dashboardPage.toolbar.syncTransactionButton).toBeVisible();

        // Stats Cards

        // Current Balance Card
        await expect(dashboardPage.currentBalanceCard.container).toBeVisible();
        await expect(dashboardPage.currentBalanceCard.title).toHaveText('Current Balance');
        await expect(dashboardPage.currentBalanceCard.amount).toHaveText('$0.00');
        await expect(dashboardPage.currentBalanceCard.badge).toHaveText('Healthy');
        // Total Income Card
        await expect(dashboardPage.totalIncomeCard.container).toBeVisible();
        await expect(dashboardPage.totalIncomeCard.title).toHaveText('Total Income');
        await expect(dashboardPage.totalIncomeCard.amount).toHaveText('$0.00');
        await expect(dashboardPage.totalIncomeCard.badge).toHaveText('0%');
        // Total Expense Card
        await expect(dashboardPage.totalExpenseCard.container).toBeVisible();
        await expect(dashboardPage.totalExpenseCard.title).toHaveText('Total Expense');
        await expect(dashboardPage.totalExpenseCard.amount).toHaveText('$0.00');
        await expect(dashboardPage.totalExpenseCard.badge).toHaveText('0%');
        // Charts
        await expect(dashboardPage.expenseByCategoryChart.container).toBeVisible();
        await expect(dashboardPage.balanceDynamicsChartContainer).toBeVisible();
        // Transactions Table
        await expect(dashboardPage.transactionsTable.rows).toHaveCount(0);
        await expect(dashboardPage.transactionsTable.header).toHaveText('Transactions');
        await expect(dashboardPage.transactionsTable.paginationContainer).toBeVisible();
        await expect(dashboardPage.transactionsTable.previousPageButton).toBeDisabled();
        await expect(dashboardPage.transactionsTable.nextPageButton).toBeDisabled();
    });

    test.describe('Charts', () => {
    test('Expense by Category chart are render correctly', async ({ page, api }) => {
        const dashboardPage = new DashboardPage(page);

        const category_food = await api.categories.getCategoryIdByName('Food');
        const category_transport = await api.categories.getCategoryIdByName('Transport');
        const category_uncategorized = await api.categories.getCategoryIdByName('Uncategorized');

        await api.transactions.createTransaction({
            title: `Chart Test Transaction - ${Date.now()}`,
            transaction_type: 'expense',
            amount: 100,
            category_id: category_food,
        });
        await api.transactions.createTransaction({
            title: `Chart Test Transaction 2 - ${Date.now()}`,
            transaction_type: 'expense',
            amount: 50,
            category_id: category_transport,
        });
        await api.transactions.createTransaction({
            title: `Chart Test Transaction 3 - ${Date.now()}`,
            transaction_type: 'expense',
            amount: 25,
            category_id: category_uncategorized,
        });

        await dashboardPage.goto();

        const chart = dashboardPage.expenseByCategoryChart.container

        await expect(chart).toBeVisible();
        await expect(chart).toHaveScreenshot('expense-by-category-chart.png');

        const foodLegendItem = dashboardPage.expenseByCategoryChart.getLegendItemByCategoryTitle('Food');
        await expect(foodLegendItem).toBeVisible();
        await expect(foodLegendItem).toContainText('Food');
        await expect(foodLegendItem).toContainText('57.1%');

        const transportLegendItem = dashboardPage.expenseByCategoryChart.getLegendItemByCategoryTitle('Transport');
        await expect(transportLegendItem).toBeVisible();
        await expect(transportLegendItem).toContainText('Transport');
        await expect(transportLegendItem).toContainText('28.6%');

        const uncategorizedLegendItem = dashboardPage.expenseByCategoryChart.getLegendItemByCategoryTitle('Uncategorized');
        await expect(uncategorizedLegendItem).toBeVisible();
        await expect(uncategorizedLegendItem).toContainText('Uncategorized');
        await expect(uncategorizedLegendItem).toContainText('14.3%');

    });

    test('Balance Dynamics chart is rendered correctly', async ({ page, api }) => {
        await page.clock.setFixedTime(new Date('2026-05-11T10:00:00Z'));
        const dashboardPage = new DashboardPage(page);

        await api.transactions.createTransaction({
            title: `Balance Chart Test Transaction 1 - ${Date.now()}`,
            transaction_type: 'income',
            created_at: '2026-04-27',
            amount: 100,
            category_id: await api.categories.getCategoryIdByName('Uncategorized'),
        });
        await api.transactions.createTransaction({
            title: `Balance Chart Test Transaction 2 - ${Date.now()}`,
            transaction_type: 'expense',
            created_at: '2026-05-04',
            amount: 50,
            category_id: await api.categories.getCategoryIdByName('Food'),
        });
        await api.transactions.createTransaction({
            title: `Balance Chart Test Transaction 3 - ${Date.now()}`,
            transaction_type: 'expense',
            created_at: '2026-05-08',
            amount: 25,
            category_id: await api.categories.getCategoryIdByName('Transport'),
        });

        await dashboardPage.goto();

        const chartContainer = dashboardPage.balanceDynamicsChartContainer;
        await expect(chartContainer).toBeVisible();
        await expect(chartContainer).toHaveScreenshot('balance-dynamics-chart.png');
    });
});

    test('User can filter transactions', async ({ page, api }) => {
        await page.clock.setFixedTime(new Date('2026-05-11T10:00:00Z'));
        const dashboardPage = new DashboardPage(page);
        const titleYesterday = 'Filter Test Transaction yesterday';
        await api.transactions.createTransaction({
            title: titleYesterday,
            transaction_type: 'expense',
            created_at: '2026-05-10', // Yesterday
            amount: 150,
            category_id: await api.categories.getCategoryIdByName('Uncategorized'),
        });
        const title7DaysAgo = 'Filter Test Transaction 7 days ago';
        await api.transactions.createTransaction({
            title: title7DaysAgo,
            transaction_type: 'income',
            created_at: '2026-05-06', // 4 days ago
            amount: 300,
            category_id: await api.categories.getCategoryIdByName('Food'),
        });
        const title8DaysAgo = 'Filter Test Transaction 8 days ago';
        await api.transactions.createTransaction({
            title: title8DaysAgo,
            transaction_type: 'expense',
            created_at: '2026-05-01', // 10 days ago
            amount: 100,
            category_id: await api.categories.getCategoryIdByName('Transport'),
        });
        const title31DaysAgo = 'Filter Test Transaction 31 days ago';
        await api.transactions.createTransaction({
            title: title31DaysAgo,
            transaction_type: 'income',
            created_at: '2026-04-01', // 31 days ago
            amount: 200,
            category_id: await api.categories.getCategoryIdByName('Salary'),
        });

        await dashboardPage.goto();
        await expect(dashboardPage.transactionsTable.rows).toHaveCount(3); // Month filter is selected by default

        // Week filter
        await dashboardPage.toolbar.filterWeek.click();
        await expect(dashboardPage.transactionsTable.rows).toHaveCount(2);

        const rowYesterday = await dashboardPage.transactionsTable.getRowByTitle(titleYesterday);
        await expect(rowYesterday).toBeVisible();
        await expect(rowYesterday).toContainText('-$150.00');
        await expect(rowYesterday).toContainText('Uncategorized');
        const row7DaysAgo = await dashboardPage.transactionsTable.getRowByTitle(title7DaysAgo);
        await expect(row7DaysAgo).toBeVisible();
        await expect(row7DaysAgo).toContainText('$300.00');
        await expect(row7DaysAgo).toContainText('Food');

        await expect(dashboardPage.totalIncomeCard.amount).toHaveText('$300.00');
        await expect(dashboardPage.totalExpenseCard.amount).toHaveText('$150.00');
        await expect(dashboardPage.currentBalanceCard.amount).toHaveText('$250.00');

        // Month filter
        await dashboardPage.toolbar.filterMonth.click();
        await expect(dashboardPage.transactionsTable.rows).toHaveCount(3);
        const row8DaysAgo = await dashboardPage.transactionsTable.getRowByTitle(title8DaysAgo);
        await expect(row8DaysAgo).toBeVisible();
        await expect(row8DaysAgo).toContainText('-$100.00');
        await expect(row8DaysAgo).toContainText('Transport');

        await expect(dashboardPage.totalIncomeCard.amount).toHaveText('$300.00');
        await expect(dashboardPage.totalExpenseCard.amount).toHaveText('$250.00');
        await expect(dashboardPage.currentBalanceCard.amount).toHaveText('$250.00');

        // All time filter
        await dashboardPage.toolbar.filterAllTime.click();
        await expect(dashboardPage.transactionsTable.rows).toHaveCount(4);
        const row31DaysAgo = await dashboardPage.transactionsTable.getRowByTitle(title31DaysAgo);
        await expect(row31DaysAgo).toBeVisible();
        await expect(row31DaysAgo).toContainText('$200.00');
        await expect(row31DaysAgo).toContainText('Salary');

        await expect(dashboardPage.totalIncomeCard.amount).toHaveText('$500.00');
        await expect(dashboardPage.totalExpenseCard.amount).toHaveText('$250.00');
        await expect(dashboardPage.currentBalanceCard.amount).toHaveText('$250.00');
});
});

