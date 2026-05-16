import { Page, Locator } from "@playwright/test";
import { RegisterRequest } from "../../interfaces/auth";
import { BasePage } from "../common/BasePage";

export class RegisterPage extends BasePage {
    protected readonly url = '/register';


    readonly title: Locator;
    // Form fields
    readonly usernameInput: Locator;
    readonly emailInput: Locator;
    readonly passwordInput: Locator;
    readonly confirmPasswordInput: Locator;
    readonly submitButton: Locator;

    readonly signInLink: Locator;



    constructor(page: Page) {
        super(page);
        this.title = page.getByRole('heading', { name: 'Create Account' });
        this.usernameInput = page.getByLabel('Username');
        this.emailInput = page.getByLabel('Email');
        this.passwordInput = page.getByLabel('Password', { exact: true });
        this.confirmPasswordInput = page.getByLabel('Confirm password');
        this.submitButton = page.getByRole('button', { name: 'Create account' });
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

}