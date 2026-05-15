import { test as baseTest, expect } from '@playwright/test';
import { ApiClient } from '../api/ApiClient';

type DynamicUserFixtures = {
    api: ApiClient;
};

export const test = baseTest.extend<DynamicUserFixtures>({

    // Clear cookies and local storage before each test to ensure a clean state
    // eslint-disable-next-line no-empty-pattern
    storageState: async ({}, use) => {
        await use({ cookies: [], origins: [] });
    },

    // Inizialize API client for each test
    api: async ({ request }, use) => {
        const apiInstance = new ApiClient(request);
        await use(apiInstance);
    },

    page: async ({ page, api }, use, testInfo) => {
        const uniqueSuffix = Date.now().toString(36) + Math.random().toString(36).substring(2, 5) + `w${testInfo.workerIndex}`;

        const uniqueEmail = `test_${uniqueSuffix}@example.com`;
        const uniqueUsername = `usr_${uniqueSuffix}`;
        
        await api.auth.register({
            username: uniqueUsername,
            email: uniqueEmail,
            password: 'TestPassword123',
            confirmPassword: 'TestPassword123'
        });

        // Log in and get cookies
        const cookies = await api.auth.loginAndGetCookies(uniqueEmail, 'TestPassword123');
        await page.context().addCookies(cookies);
        if (!api.auth.apiToken) {
            throw new Error('API token is not set after login');
        }
        api.setToken(api.auth.apiToken);
        
        // Get the page ready for the test (with authenticated user)
        await use(page);
    }
});


export { expect };