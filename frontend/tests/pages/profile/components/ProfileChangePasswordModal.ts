import { Page, Locator } from "@playwright/test";

export class ProfileChangePasswordModal {
    readonly page: Page;
    readonly container: Locator;

    readonly currentPasswordInput: Locator;
    readonly newPasswordInput: Locator;
    readonly confirmNewPasswordInput: Locator;

    readonly saveButton: Locator;
    readonly cancelButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('password-form')

        this.currentPasswordInput = this.container.getByTestId('current-password-input');
        this.newPasswordInput = this.container.getByTestId('new-password-input');
        this.confirmNewPasswordInput = this.container.getByTestId('confirm-password-input');

        this.saveButton = this.page.getByRole('button', { name: 'Save Changes' });
        this.cancelButton = this.page.getByRole('button', { name: 'Cancel' });
    }
}