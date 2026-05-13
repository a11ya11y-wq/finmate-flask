import { Page, Locator, expect } from "@playwright/test";


export class Toast {
    readonly page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    private getToastByMessage(message: string): Locator {
        return this.page.getByTestId("toast-item").filter({ hasText: message });
    }

    async expectSuccess(message: string) {
        const toast = this.getToastByMessage(message);
        await expect(toast).toBeVisible();
        await expect(toast).toHaveAttribute('data-variant', 'success');
    }

    async expectError(message: string) {
        const toast = this.getToastByMessage(message);
        await expect(toast).toBeVisible();
        await expect(toast).toHaveAttribute('data-variant', 'error');
    }

    async expectInfo(message: string) {
        const toast = this.getToastByMessage(message);
        await expect(toast).toBeVisible();
        await expect(toast).toHaveAttribute('data-variant', 'info');
    }
}