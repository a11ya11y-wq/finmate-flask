import { Page, Locator } from "@playwright/test";


export class DashboardCategoryChart {
    readonly page: Page;
    readonly container: Locator;

    readonly legendContainer: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('dashboard-expenses-by-category');
        this.legendContainer = this.page.getByTestId('expense-by-category-legend');
    }

    getLegendItemByCategoryTitle(title: string): Locator {
        if (!title || title.trim() === '') {
            throw new Error('Category title must be a non-empty string');
        }
        return this.legendContainer.locator('li').filter({ hasText: title }).first();
    }
}