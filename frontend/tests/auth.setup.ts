import { test as setup, expect } from '@playwright/test';
import { LoginPage } from './pages/auth/LoginPage';
import dotenv from 'dotenv';

dotenv.config();

const authFile = 'tests/.auth/user.json';

setup('authenticate', async ({ page }) => {
    const loginPage = new LoginPage(page);
    
    await loginPage.goto();

    const email = process.env.USER_EMAIL;
    const password = process.env.USER_PASSWORD;

    if (!email || !password) {
        throw new Error('USER_EMAIL or USER_PASSWORD is not defined in .env');
    }

    await loginPage.login(email, password);
    await expect(page).toHaveURL(/.*\/dashboard/);

    await page.context().storageState({ path: authFile });
});