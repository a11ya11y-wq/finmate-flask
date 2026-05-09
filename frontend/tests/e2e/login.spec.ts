import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';


const email = process.env.USER_EMAIL || 'testemail@gmail.com';
const password = process.env.USER_PASSWORD || 'Test123123';

test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Authentication', () => {
    test('User can login with valid credentials', async ({ page }) => {
        // Arrange
        const loginPage = new LoginPage(page);
        const dashboardPage = new DashboardPage(page);
        await loginPage.goto();

        // Act
        await loginPage.login(
            email,
            password,
        )
        // Assert
        await expect(page).toHaveURL(/.*\/dashboard/);
        await expect(dashboardPage.toolbar.title).toHaveText('Dashboard');
    })

    const invalidLoginCases = [
    { desc: 'wrong email', email: 'wrongemail@gmail.com', pass: 'Test123123', error: 'Invalid email or password.' },
    { desc: 'wrong password', email: email, pass: 'wrong', error: 'Invalid email or password.' },
];
    for (const data of invalidLoginCases) {
        test('User cannot login with ' + data.desc, async ({ page }) => {
            const loginPage = new LoginPage(page);
            await loginPage.goto();

            await loginPage.login(
                data.email,
                data.pass
            );

            await expect(loginPage.page).toHaveURL(/.*\/login/);
            await loginPage.toast.expectError(data.error);
        });
    }
    const validLoginCases = [
        { desc: 'Empty email', field: 'email', email: '', pass: '', expectedMsg: 'Please fill out this field.' },
        { desc: 'Empty password', field: 'password', email: email, pass: '', expectedMsg: 'Please fill out this field.' },
        { desc: 'Invalid email format without @', field: 'email', email: 'invalidemail', pass: password, expectedMsg: 'Please include an \'@\' in the email address. \'invalidemail\' is missing an \'@\'.' },
        { desc: 'Invalid email format without domain', field: 'email', email: 'invalid@', pass: password, expectedMsg: 'Please enter a part following \'@\'. \'invalid@\' is incomplete.' },
        // { desc: 'Short password', field: 'password', email: email, pass: 'shrt', expectedMsg: 'Password must be at least 8 characters long' }, // TODO: Implement password length validation in the frontend and update this test case accordingly
    ];
    for (const data of validLoginCases) {
        test('User cannot login with ' + data.desc, async ({ page }) => {
            const loginPage = new LoginPage(page);
            await loginPage.goto();

            await loginPage.login(
                data.email,
                data.pass
            );
            await expect(loginPage.page).toHaveURL(/.*\/login/);

            const input = data.field === 'email' ? loginPage.emailInput : loginPage.passwordInput;
            const validationMessage = await input.evaluate((el: HTMLInputElement) => el.validationMessage);

            expect(validationMessage).toBe(data.expectedMsg);
            });
    }
    const rememberMeCases = [
        { desc: 'Remember me checked', expectedDays: 30, rememberMe: true },
        { desc: 'Remember me unchecked', expectedDays: 1, rememberMe: false },
    ];
    for (const data of rememberMeCases) {
        test('Login with ' + data.desc, async ({ page }) => {
            const loginPage = new LoginPage(page);
            await loginPage.goto();

            await loginPage.login(
                email,
                password,
                data.rememberMe // rememberMe = true or false
            );
            await expect(page).toHaveURL(/.*\/dashboard/);

            const cookies = await page.context().cookies();
            const refreshCookie = cookies.find(c => c.name === 'finmate_refresh_token');

            // The refresh token should have an expiration date around 30 days in the future
            if (!refreshCookie) {
                throw new Error('Refresh token cookie not found after login');
            }
            const expires = refreshCookie.expires;
            const now = Math.floor(Date.now() / 1000);
            const diffDays = (expires - now) / (60 * 60 * 24);

            expect(diffDays).toBeGreaterThan(data.expectedDays - 1);
            expect(diffDays).toBeLessThan(data.expectedDays + 1);

        });
    }

    test('User can navigate to registration page from login page', async ({ page }) => {
        const loginPage = new LoginPage(page);
        await loginPage.goto();

        await loginPage.createOneLink.click();
        await expect(page).toHaveURL(/.*\/register/);
        });
    });