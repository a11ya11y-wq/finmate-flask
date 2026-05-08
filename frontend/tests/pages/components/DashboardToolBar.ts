import { Page, Locator } from '@playwright/test'

export class DashboardToolBar {
    readonly page: Page;
    readonly container: Locator;

    readonly title: Locator;

    // Period Filters
    readonly filterWeek: Locator;
    readonly filterMonth: Locator;
    readonly filterAllTime: Locator;

    // Navigation buttons
    readonly addTransactionButton: Locator;
    readonly syncTransactionButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('dashboard-toolbar');
        
        this.title = this.container.getByRole('heading', { name: 'Dashboard' });

        this.filterWeek = this.container.getByRole('button', { name: 'Week' });
        this.filterMonth = this.container.getByRole('button', { name: 'Month' });
        this.filterAllTime = this.container.getByRole('button', { name: 'All Time' });

        this.addTransactionButton = this.container.getByRole('button', { name: /add/i });
        this.syncTransactionButton = this.container.getByRole('button', { name: 'SYNC' });    
    };

    async selectPeriodFilter(filter: 'Week' | 'Month' | 'All Time') {
        switch (filter) {
            case 'Week':
                await this.filterWeek.click();
                break;
            case 'Month':
                await this.filterMonth.click();
                break;
            case 'All Time':
                await this.filterAllTime.click();
                break;
        };
    };
}