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

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByRole('banner'); //banner = header
        
        this.userMenuToggle = page.locator('button').filter({ has: page.locator('img[alt="Avatar"]') });
        this.dashboardOption = page.getByRole('button', { name: 'Dashboard' });
        this.budgetOption = page.getByRole('button', { name: 'Budgets' });
        this.profileOption = page.getByRole('button', { name: 'Profile' });
        this.logoutOption = page.getByRole('button', { name: 'Logout' });
    }

    async logout() {
        await this.userMenuToggle.click();
        await this.logoutOption.click();
    }

}