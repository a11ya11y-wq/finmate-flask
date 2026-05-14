import { Page, Locator } from "@playwright/test";

export class BudgetCard {
    readonly page: Page

    readonly budgetCards: Locator


    constructor(page: Page) {
        this.page = page;

        this.budgetCards = page.getByTestId('budget-card');
    }

    getBudgetCardByCategory(category: string): Locator {
        return this.budgetCards.filter({ hasText: category });
    }

    async deleteBudgetByCategory(category: string) {
        const card = await this.getBudgetCardByCategory(category);
        await card.locator('button').click(); 
}
}