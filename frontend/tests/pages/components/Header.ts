import { Page, Locator } from '@playwright/test'



export class Header {
    readonly page: Page;
    readonly container: Locator;

    // Dropdown Menu:
    readonly userMenuToggle: Locator;
    readonly dashboardOption: Locator;
    readonly budgetOption: Locator;
    readonly profileOption: Locator;
    readonly logoutOption: Locator;

    readonly userAvatar: Locator;

    readonly logo: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByRole('banner'); //banner = header
        
        this.userMenuToggle = this.container.locator('button').filter({ has: page.locator('img[alt="Avatar"]') });
        this.dashboardOption = this.container.getByRole('button', { name: 'Dashboard' });
        this.budgetOption = this.container.getByRole('button', { name: 'Budgets' });
        this.profileOption = this.container.getByRole('button', { name: 'Profile' });
        this.logoutOption = this.container.getByRole('button', { name: 'Logout' });

        this.userAvatar = this.container.getByAltText('Avatar');

        this.logo = this.container.getByAltText('FinMate');
    }

    async logout() {
        await this.userMenuToggle.click();
        await this.logoutOption.click();
    }

}