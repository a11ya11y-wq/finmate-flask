import { Page } from '@playwright/test';
import { BasePage } from './BasePage';
import { DashboardToolBar } from './components/DashboardToolBar';
import { AddTransactionModal } from './components/AddTransactionModal';
import { TransactionsTable } from './components/TransactionsTable';
import { ConfirmDeleteModal } from './components/ConfirmDeleteModal';


export class DashboardPage extends BasePage {
    readonly toolbar: DashboardToolBar;
    readonly addTransactionModal: AddTransactionModal;
    readonly transactionsTable: TransactionsTable;
    readonly confirmDeleteModal: ConfirmDeleteModal;

    constructor(page: Page) {
        super(page);
        this.toolbar = new DashboardToolBar(page);
        this.addTransactionModal = new AddTransactionModal(page);
        this.transactionsTable = new TransactionsTable(page);
        this.confirmDeleteModal = new ConfirmDeleteModal(page);
    }

    async goto() {
        await this.page.goto('/dashboard');
    }
}