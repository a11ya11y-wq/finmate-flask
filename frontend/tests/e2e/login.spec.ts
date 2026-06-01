import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/auth/LoginPage';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { step } from 'allure-js-commons';
import dotenv from 'dotenv';

dotenv.config();

const email = process.env.USER_EMAIL || 'testemail@gmail.com';
const password = process.env.USER_PASSWORD || 'Test123123';

test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Login Page Visuals', () => {
    test('Login page should display title correctly', async ({ page }) => {
        const loginPage = new LoginPage(page);
        
        await step('Navigate to the login page', async () => {
            await loginPage.goto();
        });

        await step('Verify the page title is correct', async () => {
            await expect(loginPage.title).toBeVisible();
            await expect(loginPage.title).toHaveText('Welcome Back');
        });
    });
});

test.describe('Login Actions', () => {
    test('User can login with valid credentials', async ({ page }) => {
        const loginPage = new LoginPage(page);
        const dashboardPage = new DashboardPage(page);
        
        await step('Navigate to the login page', async () => {
            await loginPage.goto();
        });

        await step('Submit the login form with valid credentials', async () => {
            await loginPage.login(email, password);
        });

        await step('Verify successful redirection to the dashboard', async () => {
            await expect(page).toHaveURL(/.*\/dashboard/);
            await expect(dashboardPage.toolbar.title).toHaveText('Dashboard');
        });
    });

    const invalidLoginCases = [
        { desc: 'wrong email', email: 'wrongemail@gmail.com', pass: 'Test123123', error: 'Invalid email or password.' },
        { desc: 'wrong password', email: email, pass: 'wrong', error: 'Invalid email or password.' },
    ];
    
    for (const data of invalidLoginCases) {
        test('User cannot login with ' + data.desc, async ({ page }) => {
            const loginPage = new LoginPage(page);
            
            await step('Navigate to the login page', async () => {
                await loginPage.goto();
            });

            await step(`Attempt to login with ${data.desc}`, async () => {
                await loginPage.login(data.email, data.pass);
            });

            await step('Verify user remains on login page and sees error toast', async () => {
                await expect(loginPage.page).toHaveURL(/.*\/login/);
                await loginPage.toast.expectError(data.error);
            });
        });
    }

    const invalidFormatCases = [
        { desc: 'Empty email', field: 'email', email: '', pass: '', expectedMsg: 'Email cannot be empty' },
        { desc: 'Empty password', field: 'password', email: email, pass: '', expectedMsg: 'Password cannot be empty' },
        { desc: 'Invalid email format without @', field: 'email', email: 'invalidemail', pass: password, expectedMsg: 'Enter a valid email' },
        { desc: 'Invalid email format without domain', field: 'email', email: 'invalid@', pass: password, expectedMsg: 'Enter a valid email' },
    ];
    
    for (const data of invalidFormatCases) {
        test('User cannot login with ' + data.desc, async ({ page }) => {
            const loginPage = new LoginPage(page);
            
            await step('Navigate to the login page', async () => {
                await loginPage.goto();
            });

            await step(`Attempt to login with ${data.desc}`, async () => {
                await loginPage.login(data.email, data.pass);
            });

            await step('Verify validation error under the input field', async () => {
                await expect(loginPage.page).toHaveURL(/.*\/login/);
                await loginPage.expectFieldError(data.field, data.expectedMsg);
            });
        });
    }

    const rememberMeCases = [
        { desc: 'Remember me checked', expectedDays: 30, rememberMe: true },
        { desc: 'Remember me unchecked', expectedDays: 1, rememberMe: false },
    ];
    
    for (const data of rememberMeCases) {
        test('Login with ' + data.desc, async ({ page }) => {
            const loginPage = new LoginPage(page);
            let refreshCookie;
            
            await step('Navigate to the login page', async () => {
                await loginPage.goto();
            });

            await step(`Login with Remember Me set to: ${data.rememberMe}`, async () => {
                await loginPage.login(email, password, data.rememberMe);
                await expect(page).toHaveURL(/.*\/dashboard/);
            });

            await step('Verify refresh token cookie expiration date', async () => {
                const cookies = await page.context().cookies();
                refreshCookie = cookies.find(c => c.name === 'finmate_refresh_token');

                if (!refreshCookie) {
                    throw new Error('Refresh token cookie not found after login');
                }
                
                const expires = refreshCookie.expires;
                const now = Math.floor(Date.now() / 1000);
                const diffDays = (expires - now) / (60 * 60 * 24);

                expect(diffDays).toBeGreaterThan(data.expectedDays - 1);
                expect(diffDays).toBeLessThan(data.expectedDays + 1);
            });
        });
    }

    test('User can navigate to registration page from login page', async ({ page }) => {
        const loginPage = new LoginPage(page);
        
        await step('Navigate to the login page', async () => {
            await loginPage.goto();
        });

        await step('Click on the "Create one" link', async () => {
            await loginPage.createOneLink.click();
        });

        await step('Verify redirection to the register page', async () => {
            await expect(page).toHaveURL(/.*\/register/);
        });
    });
});