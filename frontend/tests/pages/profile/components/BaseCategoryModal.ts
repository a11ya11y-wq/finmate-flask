import { Page, Locator } from '@playwright/test';



export class BaseCategoryModal {
    readonly page: Page;
    readonly container: Locator;

    readonly nameInput: Locator;
    readonly mccCodeInput: Locator;
    readonly iconSelect: Locator;
    
    readonly cancelButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('category-form');

        this.nameInput = this.container.getByLabel('Name');
        this.mccCodeInput = this.container.getByLabel('MCC Code');
        this.iconSelect = this.container.locator('.grid button');

        this.cancelButton = this.page.getByRole('button', { name: 'Cancel' });

    }

    async selectIconByIndex(index: number) {
        await this.iconSelect.nth(index).click();
    }
}