import { Page, Locator } from '@playwright/test'
import { Toast } from '../common/components/Toast';


export class LoginPage {
    readonly page: Page;
    readonly emailInput: Locator;
    readonly passwordInput: Locator;
    readonly submitButton: Locator;
    readonly rememberMeCheckbox: Locator;
    readonly toast: Toast;
    readonly createOneLink: Locator;
    readonly title: Locator;

    constructor(page: Page) {
        this.page = page;
        this.emailInput = page.getByRole('textbox', { name: 'Email' });
        this.passwordInput = page.getByRole('textbox', { name: 'Password' });
        this.submitButton = page.getByRole('button', { name: 'Sign in' });
        this.rememberMeCheckbox = page.getByRole('checkbox', { name: 'Remember me' });
        this.toast = new Toast(page);
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
    
    async getValidationMessage(fieldName: 'email' | 'password'): Promise<string | false> {
        const inputs: Record<typeof fieldName, Locator> = {
            email: this.emailInput,
            password: this.passwordInput
        };
        const inputLocator = inputs[fieldName];
        const validationMessage = await inputLocator.evaluate((el: HTMLInputElement) => el.validationMessage);
        if (!validationMessage) {
            return false;
        }
        return validationMessage;
    }
}