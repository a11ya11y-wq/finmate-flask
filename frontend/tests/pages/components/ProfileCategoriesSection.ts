import { Page, Locator } from "@playwright/test";


export class ProfileCategoriesSection {
    readonly page: Page;
    readonly container: Locator;

    readonly addNewButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('categories-section');

        this.addNewButton = this.container.getByRole('button', { name: 'Add New' });
    }

    async getCategoryCardByName(name: string) {
        return this.container.locator('.group').filter({ hasText: name });
    }

    async OpenEditModalFor(name: string) {
        const categoryCard = await this.getCategoryCardByName(name);
        await categoryCard.hover();
        await categoryCard.getByTestId('edit-category-button').click();
    }

    async OpenDeleteModalFor(name: string) {
        const categoryCard = await this.getCategoryCardByName(name);
        await categoryCard.hover();
        await categoryCard.getByTestId('delete-category-button').click();
    }
}