import { Page, Locator } from "@playwright/test";
import { Toast } from "../common/components/Toast";
import { RegisterField, RegisterRequest } from "../../interfaces/auth";


export class RegisterPage {
    readonly page: Page;
    readonly title: Locator;
    // Form fields
    readonly usernameInput: Locator;
    readonly emailInput: Locator;
    readonly passwordInput: Locator;
    readonly confirmPasswordInput: Locator;
    readonly submitButton: Locator;
    
    readonly toast: Toast;
    readonly signInLink: Locator;



    constructor(page: Page) {
        this.page = page;
        this.title = page.getByRole('heading', { name: 'Create Account' });
        this.usernameInput = page.getByLabel('Username');
        this.emailInput = page.getByLabel('Email');
        this.passwordInput = page.getByLabel('Password', { exact: true });
        this.confirmPasswordInput = page.getByLabel('Confirm password');
        this.submitButton = page.getByRole('button', { name: 'Create account' });
        this.toast = new Toast(page);
        this.signInLink = page.getByRole('link', { name: 'Sign in' });
    }

    async register(data: Partial<RegisterRequest>) {
        if (data.username) {
            await this.usernameInput.fill(data.username);
        }
        if (data.email) {
            await this.emailInput.fill(data.email);
        }
        if (data.password) {
            await this.passwordInput.fill(data.password);
        }
        if (data.confirmPassword) {
            await this.confirmPasswordInput.fill(data.confirmPassword);
        }
        await this.submitButton.click();
    }

    async goto() {
        await this.page.goto('/register');
    }

    async getValidationMessage(fieldName: RegisterField['name']): Promise<boolean | string> {
        const inputs: Record<typeof fieldName, Locator> = {
            username: this.usernameInput,
            email: this.emailInput,
            password: this.passwordInput,
            confirmPassword: this.confirmPasswordInput
        };
        const inputLocator = inputs[fieldName];
        const validationMessage = await inputLocator.evaluate((el: HTMLInputElement) => el.validationMessage);
        if (!validationMessage) {
            return false;
        }
        return validationMessage;
    }
}