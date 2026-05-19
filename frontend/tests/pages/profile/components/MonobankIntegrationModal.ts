import { Page, Locator } from "@playwright/test";


export class MonobankIntegrationModal {
    readonly page: Page;

    readonly apiKeyInput: Locator;

    readonly saveButton: Locator;
    readonly cancelButton: Locator;
    readonly disconnectMonotoken: Locator;

    constructor(page: Page) {
        this.page = page;
        this.apiKeyInput = this.page.getByLabel('API Token');

        this.saveButton = this.page.getByRole('button', { name: 'Save Changes' });
        this.cancelButton = this.page.getByRole('button', { name: 'Cancel' });
        this.disconnectMonotoken = this.page.getByRole('button', { name: 'Disconnect Monobank' });
    }
}