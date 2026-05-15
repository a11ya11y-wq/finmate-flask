import { Page, Locator } from "@playwright/test";


export class ProfileUserInfo {
    readonly page: Page;
    readonly container: Locator;

    readonly username: Locator;
    readonly email: Locator;
    readonly currency: Locator;
    readonly avatar: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('profile-user-info-container');
        this.username = this.container.getByTestId('profile-username');
        this.email = this.container.getByTestId('profile-email');
        this.currency = this.container.getByTestId('profile-currency');
        this.avatar = this.container.getByRole('img', { name: 'Avatar' });
    }
}