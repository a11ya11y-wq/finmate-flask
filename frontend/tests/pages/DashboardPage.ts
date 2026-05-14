import { Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';
import { DashboardToolBar } from './components/DashboardToolBar';
import { AddTransactionModal } from './components/AddTransactionModal';
import { EditTransactionModal } from './components/EditTransactionModal';
import { TransactionsTable } from './components/TransactionsTable';
import { ConfirmDeleteModal } from './components/ConfirmDeleteModal';
import { StatsCard } from './components/StatsCard';
import { DashboardCategoryChart } from './components/DashboardCategoryChart';

export class DashboardPage extends BasePage {
    readonly toolbar: DashboardToolBar;
    readonly addTransactionModal: AddTransactionModal;
    readonly transactionsTable: TransactionsTable;
    readonly confirmDeleteModal: ConfirmDeleteModal;
    readonly editTransactionModal: EditTransactionModal;
    // Stats cards
    readonly currentBalanceCard: StatsCard;
    readonly totalIncomeCard: StatsCard;
    readonly totalExpenseCard: StatsCard;

    // Expense by category chart
    readonly expenseByCategoryChart: DashboardCategoryChart

    // Balance dyamics chart
    readonly balanceDynamicsChartContainer: Locator;

    constructor(page: Page) {
        super(page);
        this.toolbar = new DashboardToolBar(page);

        this.currentBalanceCard = new StatsCard(page, 'dashboard-current-balance');
        this.totalIncomeCard = new StatsCard(page, 'dashboard-total-income');
        this.totalExpenseCard = new StatsCard(page, 'dashboard-total-expense');

        this.transactionsTable = new TransactionsTable(page);

        this.expenseByCategoryChart = new DashboardCategoryChart(page);
        
        this.balanceDynamicsChartContainer = this.page.getByTestId('dashboard-balance-dynamics');

        this.addTransactionModal = new AddTransactionModal(page);
        this.confirmDeleteModal = new ConfirmDeleteModal(page);
        this.editTransactionModal = new EditTransactionModal(page);

    }

    async goto() {
        await this.page.goto('/dashboard');
    }

}