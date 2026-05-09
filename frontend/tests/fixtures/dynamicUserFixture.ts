import { test as baseTest, expect } from '@playwright/test';
import { ApiClient } from '../api/ApiClient';

type DynamicUserFixtures = {
    api: ApiClient;
};

export const test = baseTest.extend<DynamicUserFixtures>({

    // Clear cookies and local storage before each test to ensure a clean state
    storageState: async (options, use) => {
        await use({ cookies: [], origins: [] });
    },

    // Inizialize API client for each test
    api: async ({ request }, use) => {
        const apiInstance = new ApiClient(request);
        await use(apiInstance);
    },

    page: async ({ page, api }, use) => {
        // Before each test, register a new user and log in to get cookies
        const uniqueEmail = `testuser_${Date.now()}@example.com`;
        
        await api.auth.register({
            username: 'testuser_' + Date.now(),
            email: uniqueEmail,
            password: 'TestPassword123',
            confirmPassword: 'TestPassword123'
        });

        // Log in and get cookies
        const cookies = await api.auth.loginAndGetCookies(uniqueEmail, 'TestPassword123');
        await page.context().addCookies(cookies);
        api.setToken(api.auth.apiToken!);
        
        // Get the page ready for the test (with authenticated user)
        await use(page);
    }
});


export { expect };