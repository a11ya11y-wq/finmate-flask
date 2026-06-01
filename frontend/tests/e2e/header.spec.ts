import { test, expect } from '../fixtures/dynamicUserFixture';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { step } from 'allure-js-commons';

test.describe('Header Navigation', () => {

    test.beforeEach(async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await step('Precondition: Navigate to dashboard and open user menu', async () => {
            await dashboardPage.goto();
            await expect(page).toHaveURL(/.*\/dashboard/);

            await page.waitForLoadState('networkidle'); 
            
            await dashboardPage.header.userMenuToggle.click();
        });
    });

    test('Navigate to Budgets from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await step('Click on Budgets option and verify navigation', async () => {
            await dashboardPage.header.budgetOption.click();
            await expect(page).toHaveURL(/.*\/budgets/);
        });
    });

    test('Navigate to Profile from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await step('Click on Profile option and verify navigation', async () => {
            await dashboardPage.header.profileOption.click();
            await expect(page).toHaveURL(/.*\/profile/);
        });
    });

    test('Logout from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await step('Click on Logout option and verify redirection to login', async () => {
            await dashboardPage.header.logoutOption.click();
            await expect(page).toHaveURL(/.*\/login/);
        });
    });

    test('Navigate to Dashboard from header', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);
        
        await step('Navigate away to Budgets page first', async () => {
            await dashboardPage.header.budgetOption.click();
            await expect(page).toHaveURL(/.*\/budgets/);
            await page.waitForLoadState('networkidle');
        });

        await step('Open user menu again and navigate back to Dashboard', async () => {
            await dashboardPage.header.userMenuToggle.click();
            await dashboardPage.header.dashboardOption.click();
            await expect(page).toHaveURL(/.*\/dashboard/);
        });
    });
});