import { Page, Locator } from '@playwright/test'



export class Header {
    readonly page: Page;
    readonly container: Locator;

    // Dropdown Menu:
    readonly userMenuToggle: Locator;
    readonly userMenuContainer: Locator;

    readonly dashboardOption: Locator;
    readonly budgetOption: Locator;
    readonly profileOption: Locator;
    readonly logoutOption: Locator;

    readonly userAvatar: Locator;
    readonly logo: Locator;

    readonly installPwaButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByRole('banner'); //banner = header
        
        this.userMenuToggle = this.container.getByTestId('user-menu-toggle');
        this.userMenuContainer = this.page.getByTestId('user-menu-container');

        this.dashboardOption = this.userMenuContainer.getByRole('link', { name: 'Dashboard' });
        this.budgetOption = this.userMenuContainer.getByRole('link', { name: 'Budgets' });
        this.profileOption = this.userMenuContainer.getByRole('link', { name: 'Profile' });
        this.logoutOption = this.userMenuContainer.getByTestId('logout-button');

        this.userAvatar = this.userMenuToggle.getByAltText('Avatar');

        this.logo = this.container.getByAltText('FinMate');
        
        this.installPwaButton = this.container.locator('button[title="Install App"]');
    }

    async logout() {
        await this.userMenuToggle.click();
        await this.logoutOption.click();
    }

    async simulatePwaInstallPrompt() {
        await this.page.evaluate(() => {
            const event = new Event('beforeinstallprompt') as any;
            event.prompt = () => { (window as any).__PWA_PROMPT_CALLED = true; };
            event.userChoice = Promise.resolve({ outcome: 'accepted' });
            window.dispatchEvent(event);
        });
    }

    async wasPwaPromptCalled(): Promise<boolean> {
        return await this.page.evaluate(() => (window as any).__PWA_PROMPT_CALLED === true);
    }
}