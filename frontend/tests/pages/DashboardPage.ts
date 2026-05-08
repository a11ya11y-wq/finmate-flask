import { Page } from '@playwright/test';
import { BasePage } from './BasePage';
import { DashboardToolBar } from './components/DashboardToolBar';
import { AddTransactionModal } from './components/AddTransactionModal';



export class DashboardPage extends BasePage {
    readonly toolbar: DashboardToolBar;
    readonly addTransactionModal: AddTransactionModal;

    constructor(page: Page) {
        super(page);
        this.toolbar = new DashboardToolBar(page);
        this.addTransactionModal = new AddTransactionModal(page);
    }

    async goto() {
        await this.page.goto('/dashboard');
    }
}