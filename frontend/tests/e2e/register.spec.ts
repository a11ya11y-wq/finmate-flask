import { test, expect } from '@playwright/test';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { RegisterField } from '../interfaces/auth';
import { ApiClient } from '../api/ApiClient';

test.use({ storageState: { cookies: [], origins: [] } });

// Helper function to generate unique strings for email and username
const generateUniqueStr = () => Date.now().toString(36) + Math.random().toString(36).substring(2, 5);

test.describe('Register Page Visuals', () => {
    test('Register page should display title correctly', async ({ page }) => {
        const registerPage = new RegisterPage(page);
        await registerPage.goto();
        await expect(registerPage.title).toBeVisible();
        await expect(registerPage.title).toHaveText('Create Account');
    });
});

test.describe('Register Actions', () => {
    test('User can register with valid credentials', async ({ page }) => {
        const registerPage = new RegisterPage(page);
        await registerPage.goto();

        const uniqueSuffix = generateUniqueStr();
        const email = `newuser_${uniqueSuffix}@example.com`;
        const username = `newuser_${uniqueSuffix}`;
        
        await registerPage.register({
            username: username,
            email: email,
            password: 'Password123!',
            confirmPassword: 'Password123!'
        });

        await expect(page).toHaveURL(/.*\/dashboard/);
    });

    const clientValidationCases = [
        { desc: 'Invalid email format', field: 'email', username: 'user', email: 'invalidemail', password: 'P123123', confirmPassword: 'P123123', expectedMsg: 'Please include an \'@\' in the email address. \'invalidemail\' is missing an \'@\'.' },
        { desc: 'Empty username', field: 'username', username: '', email: 'newuser@example.com', password: 'P123123', confirmPassword: 'P123123', expectedMsg: 'Please fill out this field.' },
        { desc: 'Empty email', field: 'email', username: 'user', email: '', password: 'P123123', confirmPassword: 'P123123', expectedMsg: 'Please fill out this field.' },
        { desc: 'Empty password', field: 'password', username: 'user', email: 'newuser@example.com', password: '', confirmPassword: '', expectedMsg: 'Please fill out this field.' },
        { desc: 'Empty confirm password', field: 'confirmPassword', username: 'user', email: 'newuser@example.com', password: 'P123123', confirmPassword: '', expectedMsg: 'Please fill out this field.' },
    ];
    
    for (const data of clientValidationCases) {
        test('(Client Validation)User cannot register with ' + data.desc, async ({ page }) => {
            const registerPage = new RegisterPage(page);
            await registerPage.goto();

            await registerPage.register({
                username: data.username,
                email: data.email,
                password: data.password,
                confirmPassword: data.confirmPassword
            });

            await expect(registerPage.page).toHaveURL(/.*\/register/);

            const validationMessage = await registerPage.getValidationMessage(data.field as RegisterField['name']);
            expect(validationMessage).toBe(data.expectedMsg);
        });
    }

    const serverValidationCases = [
        { desc: 'Pass & conf_pass do not match', field: 'confirmPassword', username: 'user', email: 'newuser@example.com', password: 'P123123', confirmPassword: 'P1231234', expectedMsg: 'Passwords do not match.' },
        { desc: 'Short password', field: 'password', username: 'user', email: 'newuser@example.com', password: 'P123', confirmPassword: 'P123', expectedMsg: 'String should have at least 6 characters' },
        { desc: 'Username too short', field: 'username', username: 'usr', email: 'newuser@example.com', password: 'P123123', confirmPassword: 'P123123', expectedMsg: 'String should have at least 4 characters' },
        { desc: 'Username too long', field: 'username', username: 'u'.repeat(33), email: 'newuser@example.com', password: 'P123123', confirmPassword: 'P123123', expectedMsg: 'String should have at most 32 characters' },
        { desc: 'Password too long', field: 'password', username: 'user', email: 'newuser@example.com', password: 'P'.repeat(33), confirmPassword: 'P'.repeat(33), expectedMsg: 'String should have at most 32 characters' },
    ];
    
    for (const data of serverValidationCases) {
        test('(Server Validation) User cannot register with ' + data.desc, async ({ page }) => {
            const registerPage = new RegisterPage(page);
            await registerPage.goto();

            await registerPage.register({
                username: data.username,
                email: data.email,
                password: data.password,
                confirmPassword: data.confirmPassword
            });

            await expect(registerPage.page).toHaveURL(/.*\/register/);
            await registerPage.toast.expectError(data.expectedMsg!);
        });
    }

    const duplicateData = [
        { desc: 'email', fieldToDuplicate: 'email', expectedMessage: 'Email already registered.'},
        { desc: 'username', fieldToDuplicate: 'username', expectedMessage: 'Username already registered'},
    ];
    
    for (const data of duplicateData) {
        test('User cannot register with duplicate data: ' + data.desc, async ({ page, request }) => {
            const registerPage = new RegisterPage(page);
            const api = new ApiClient(request);

            const originalEmail = `uniqueemail_${generateUniqueStr()}@example.com`;
            const originalUsername = `uniqueuser_${generateUniqueStr()}`;

            await api.auth.register({
                username: originalUsername,
                email: originalEmail,
                password: 'Password123!',
                confirmPassword: 'Password123!'
            });

            await registerPage.goto();

            await registerPage.register({
                username: data.fieldToDuplicate === 'email' ? `existinguser_${generateUniqueStr()}` : originalUsername, // Condition ? Value_If_True : Value_If_False
                email: data.fieldToDuplicate === 'email' ? originalEmail : `existinguser_${generateUniqueStr()}@example.com`,
                password: 'Password123!',
                confirmPassword: 'Password123!'
            });

            await expect(registerPage.page).toHaveURL(/.*\/register/);
            await registerPage.toast.expectError(data.expectedMessage);
        });
    }

    test('User can navigate to login page from register page', async ({ page }) => {
        const registerPage = new RegisterPage(page);
        await registerPage.goto();

        await registerPage.signInLink.click();
        await expect(registerPage.page).toHaveURL(/.*\/login/);
    });
});