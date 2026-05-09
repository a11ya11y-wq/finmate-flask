import { Page, Locator } from "@playwright/test";


export class ConfirmDeleteModal {
    readonly page: Page; // TODO: Refactor to use container like in AddTransactionModal

    //Buttons
    readonly deleteButton: Locator;
    readonly cancelButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.deleteButton = page.getByRole('button', { name: /delete/i });
        this.cancelButton = page.getByRole('button', { name: /cancel/i });
    }
}