import { test, expect } from '../fixtures/dynamicUserFixture';
import { DashboardPage } from '../pages/dashboard/DashboardPage';

test.describe('Header Navigation', () => {
    test.beforeEach(async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        await dashboardPage.goto();
        await expect(page).toHaveURL(/.*\/dashboard/);

        await page.waitForLoadState('networkidle'); // Ensure all network requests are finished and the page is fully loaded
        
        await dashboardPage.header.userMenuToggle.click();
    });

    test('Navigate to Budgets from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        await dashboardPage.header.budgetOption.click();
        await expect(page).toHaveURL(/.*\/budgets/);
    });

    test('Navigate to Profile from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        await dashboardPage.header.profileOption.click();
        await expect(page).toHaveURL(/.*\/profile/);
    });

    test('Logout from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        await dashboardPage.header.logoutOption.click();
        await expect(page).toHaveURL(/.*\/login/);
    });

    test('Navigate to Dashboard from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await dashboardPage.header.budgetOption.click();
        await expect(page).toHaveURL(/.*\/budgets/);

        await page.waitForLoadState('networkidle');

        await dashboardPage.header.userMenuToggle.click();
        await dashboardPage.header.dashboardOption.click();
        await expect(page).toHaveURL(/.*\/dashboard/);
    });
});