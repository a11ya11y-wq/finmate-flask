import { Page, Locator } from '@playwright/test'
import { Toast } from './components/Toast';


export class LoginPage {
    readonly page: Page;
    readonly emailInput: Locator;
    readonly passwordInput: Locator;
    readonly submitButton: Locator;
    readonly rememberMeCheckbox: Locator;
    readonly toast: Toast;
    readonly createOneLink: Locator;

    constructor(page: Page) {
        this.page = page;
        this.emailInput = page.getByRole('textbox', { name: 'Email' });
        this.passwordInput = page.getByRole('textbox', { name: 'Password' });
        this.submitButton = page.getByRole('button', { name: 'Sign in' });
        this.rememberMeCheckbox = page.getByRole('checkbox', { name: 'Remember me' });
        this.toast = new Toast(page);
        this.createOneLink = page.getByRole('link', { name: 'Create one' });
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