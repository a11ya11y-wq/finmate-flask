import { Page, Locator } from "@playwright/test";


export class EditProfileModal {
    readonly page: Page;
    readonly container: Locator;

    readonly usernameInput: Locator;
    readonly currencySelect: Locator;
    readonly avatarOptions: Locator;

    readonly saveButton: Locator;
    readonly cancelButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('edit-profile-form');

        this.usernameInput = this.container.getByLabel('Username');
        this.currencySelect = this.container.getByLabel('Preferred Currency');
        this.avatarOptions = this.container.locator('button.group.relative');

        this.saveButton = page.getByRole('button', { name: 'Save Changes' });
        this.cancelButton = page.getByRole('button', { name: 'Cancel' });
    }

    async selectAvatarByIndex(index: number) {
        await this.avatarOptions.nth(index).click();
    }
}