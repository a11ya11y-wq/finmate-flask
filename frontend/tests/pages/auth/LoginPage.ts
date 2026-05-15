import { Page, Locator } from '@playwright/test'
import { BasePage } from '../common/BasePage';

export class LoginPage extends BasePage {
    readonly emailInput: Locator;
    readonly passwordInput: Locator;
    readonly submitButton: Locator;
    readonly rememberMeCheckbox: Locator;
    readonly createOneLink: Locator;
    readonly title: Locator;

    constructor(page: Page) {
        super(page);
        this.emailInput = page.getByRole('textbox', { name: 'Email' });
        this.passwordInput = page.getByRole('textbox', { name: 'Password' });
        this.submitButton = page.getByRole('button', { name: 'Sign in' });
        this.rememberMeCheckbox = page.getByRole('checkbox', { name: 'Remember me' });
        this.createOneLink = page.getByRole('link', { name: 'Create one' });
        this.title = page.getByRole('heading', { name: 'Welcome Back' });
    }

    async goto() {
        await this.page.goto('/login');
    }

    async login(email: string, password: string, rememberMe: boolean = false) {
        await this.emailInput.fill(email);
        await this.passwordInput.fill(password);
        if (rememberMe) {
            await this.rememberMeCheckbox.check();
        }
        await this.submitButton.click();
    }
}