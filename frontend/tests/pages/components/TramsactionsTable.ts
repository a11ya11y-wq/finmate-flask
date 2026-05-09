import { Page, Locator } from "@playwright/test";


export class TransactionsTable {
    readonly page: Page;
    readonly container: Locator;

    readonly rows: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('transactions-table');
        this.rows = this.container.getByTestId('transaction-row'); // Array of rows
    }

    async getRowByTitle(title: string): Promise<Locator> {
        return this.rows.filter({ hasText: title }).first();
    }

    async openDeleteModalFor(title: string) {
        const row = await this.getRowByTitle(title);
        await row.getByTitle('Delete').click();
    }

    async openEditModalFor(title: string) {
        const row = await this.getRowByTitle(title);
        await row.getByTitle('Edit').click();
    }
}