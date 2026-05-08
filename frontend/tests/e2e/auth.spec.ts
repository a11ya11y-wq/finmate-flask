import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';


test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Authentication', () => {
    test('User can login with valid credentials', async ({ page }) => {
        // Arrange
        const loginPage = new LoginPage(page);
        const dashboardPage = new DashboardPage(page);
        await loginPage.goto();

        // Act
        await loginPage.login(
            'demotest@gmail.com',
            '123123',
        )
        // Assert
        await expect(page).toHaveURL(/.*\/dashboard/);
        await expect(dashboardPage.toolbar.title).toHaveText('Dashboard');
    })
}); 