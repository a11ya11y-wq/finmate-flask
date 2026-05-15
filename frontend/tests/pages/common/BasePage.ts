import { expect, Page } from '@playwright/test'
import { Header } from './components/Header';
import { Toast } from './components/Toast';


export class BasePage {
    readonly page: Page
    readonly header: Header
    readonly toast: Toast

    constructor(page: Page) {
        this.page = page;
        this.header = new Header(page);
        this.toast = new Toast(page);
    }

    // Common method to check for field-validation error messages
    async expectFieldError(fieldName: string, expectedMessage: string) { 
        const errorLocator = this.page.getByTestId(`${fieldName}-error`);
    
        await expect(errorLocator).toBeVisible({ timeout: 5000 });
        await expect(errorLocator).toHaveText(expectedMessage);
    }
}