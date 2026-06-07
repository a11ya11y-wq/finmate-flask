import { Page, Locator } from "@playwright/test";


export class TransactionsTable {
    readonly page: Page;
    readonly container: Locator;

    readonly header: Locator;

    //Pagination
    readonly paginationContainer: Locator;
    readonly previousPageButton: Locator;
    readonly nextPageButton: Locator;

    readonly rows: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('transactions-table');
        
        this.header = this.container.getByRole('heading', { name: 'Transactions', exact: true });

        // Pagination
        this.paginationContainer = this.container.getByTestId('transactions-table-pagination');
        this.previousPageButton = this.paginationContainer.getByRole('button', { name: 'Prev' });
        this.nextPageButton = this.paginationContainer.getByRole('button', { name: 'Next' });

        this.rows = this.container.getByTestId('transaction-row'); // Array of rows

    }

    async getRowByTitle(title: string): Promise<Locator> {
        if (!title || title.trim() === '') {
            throw new Error('Title must be a non-empty string');
        }
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