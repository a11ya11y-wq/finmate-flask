import { test, expect } from '../fixtures/dynamicUserFixture';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { step } from 'allure-js-commons';

test.describe('PWA Install Button', () => {
    test('Should display Install button when beforeinstallprompt is fired on Android/Desktop', async ({ page }) => {
        const dashboardPage = new DashboardPage(page);

        await step('Navigate to dashboard', async () => {
            await dashboardPage.goto();
            await expect(page).toHaveURL(/.*\/dashboard/);
        });

        await step('Verify install button is not visible initially', async () => {
            await expect(dashboardPage.header.installPwaButton).toBeHidden();
        });

        await step('Simulate beforeinstallprompt event', async () => {
            await dashboardPage.header.simulatePwaInstallPrompt();
        });

        await step('Verify Install button becomes visible', async () => {
            await expect(dashboardPage.header.installPwaButton).toBeVisible();
        });

        await step('Click install button and verify prompt logic is triggered', async () => {
            await dashboardPage.header.installPwaButton.click();
            
            // Verify that the browser's native prompt() method would have been called
            expect(await dashboardPage.header.wasPwaPromptCalled()).toBeTruthy();
            
            // Verify button disappears after "accepting" the mock prompt
            await expect(dashboardPage.header.installPwaButton).toBeHidden();
        });
    });
});
