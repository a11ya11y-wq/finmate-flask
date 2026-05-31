import { test, expect } from '../fixtures/dynamicUserFixture';
import { ReportsPage } from '../pages/reports/ReporstPage';
import { step } from 'allure-js-commons';
import path from 'path';
import fs from 'fs';



test.describe('Reports Page', () => {

    test('User can generate a report for the last month using quick range selection', async ({ page, api }) => {

        const reportsPage = new ReportsPage(page);

        await step('Create a transaction in the last month to ensure there is data for the report', async () => {

            const cat_id = await api.categories.getCategoryIdByName('Food');
            await api.transactions.createTransaction({
                amount: 100,
                transaction_type: 'income',
                created_at: '2026-05-25T12:00:00Z',
                title: 'Test Transaction for Report',
                category_id: cat_id,
            });

            await page.clock.setFixedTime(new Date('2026-05-30T12:00:00Z'));
        });

        await step('Generate a report for the last month and verify the results', async () => {

            await reportsPage.goto();

            await reportsPage.quickRangeMonthButton.click();
            await reportsPage.generateReportButton.click();

            await expect(reportsPage.generateReportFormSuccessContainer).toBeVisible({ timeout: 10000 });
            await expect(reportsPage.generateReportFormSuccessTitle).toHaveText('Report is ready');
            await expect(reportsPage.generateReportFormSuccessPeriod).toHaveText(/Period: May 01, 2026 - May 30, 2026/);

            const row = await reportsPage.getFirstProcessedReportRow();
            await expect(row).toContainText('Processed', { ignoreCase: true });
            await expect(row).toContainText('May 30, 2026');
        });

        await step('Download the generated report and verify the file', async () => {
        
            await expect(reportsPage.downloadReportButton).toBeVisible();

            const downloadPromise = page.waitForEvent('download');

            await reportsPage.downloadReportButton.click();

            const download = await downloadPromise;
            const fileName = download.suggestedFilename();
            expect(fileName).toMatch(/.*\.pdf$/);
            const downloadPath = path.join(test.info().outputDir, fileName);
            await download.saveAs(downloadPath);

            expect(fs.existsSync(downloadPath)).toBeTruthy();
            const stats = fs.statSync(downloadPath);
            expect(stats.size).toBeGreaterThan(1000);
        });
    });

    test('User can generate a report for a custom date range', async ({ page, api }) => {

        const reportsPage = new ReportsPage(page);

        await step('Create transactions in the specified date range to ensure there is data for the report', async () => {

            const cat_id = await api.categories.getCategoryIdByName('Utilities');
            await api.transactions.createTransaction({
                amount: 50,
                transaction_type: 'expense',
                created_at: '2026-04-10T12:00:00Z',
                title: 'Test Transaction for Custom Report',
                category_id: cat_id,
            });
            await api.transactions.createTransaction({
                amount: 75,
                transaction_type: 'expense',
                created_at: '2026-04-20T12:00:00Z',
                title: 'Another Test Transaction for Custom Report',
                category_id: cat_id,
            });

            await page.clock.setFixedTime(new Date('2026-04-25T12:00:00Z'));

        });

        await step('Generate a report for the custom date range and verify the results', async () => {
            await reportsPage.goto();
            await reportsPage.reportStartDateInput.fill('2026-04-01');
            await reportsPage.reportEndDateInput.fill('2026-04-30');
            await reportsPage.generateReportButton.click();

            await expect(reportsPage.generateReportFormSuccessContainer).toBeVisible({ timeout: 10000 });
            await expect(reportsPage.generateReportFormSuccessTitle).toHaveText('Report is ready');
            await expect(reportsPage.generateReportFormSuccessPeriod).toHaveText(/Period: Apr 01, 2026 - Apr 30, 2026/);

            const row = await reportsPage.getFirstProcessedReportRow();
            await expect(row).toContainText('Processed', { ignoreCase: true });
            await expect(row).toContainText('Apr 01, 2026 - Apr 30, 2026');
        });

        await step('Download the generated report and verify the file', async () => {

            await expect(reportsPage.downloadReportButton).toBeVisible();
            const downloadPromise = page.waitForEvent('download');
            await reportsPage.downloadReportButton.click();

            const download = await downloadPromise;
            const fileName = download.suggestedFilename();
            expect(fileName).toMatch(/.*\.pdf$/);

            const downloadPath = path.join(test.info().outputDir, fileName);
            await download.saveAs(downloadPath);

            expect(fs.existsSync(downloadPath)).toBeTruthy();
            const stats = fs.statSync(downloadPath);
            expect(stats.size).toBeGreaterThan(1000);
        });

    });

    test('User cant generate a report without transactions in the selected period', async ({ page }) => {

        const reportsPage = new ReportsPage(page);

        await step('Generate a report for a period with no transactions and verify the error message', async () => {
            await reportsPage.goto();
            await reportsPage.reportStartDateInput.fill('2025-01-01');
            await reportsPage.reportEndDateInput.fill('2025-01-31');
            await reportsPage.generateReportButton.click();

            await reportsPage.toast.expectError('No transactions found for the specified period for report.');

            await expect(reportsPage.generateReportFormSuccessContainer).not.toBeVisible();
        });
    
    });

    test('User cannot generate a report with invalid date range', async ({ page }) => {

        const reportsPage = new ReportsPage(page);

        await step('Attempt to generate a report with an invalid date range and verify the error message', async () => {
            await reportsPage.goto();
            await reportsPage.reportStartDateInput.fill('2026-05-10');
            await reportsPage.reportEndDateInput.fill('2026-05-01');
            await reportsPage.generateReportButton.click();

            await reportsPage.toast.expectWarning('Start date must be before the end date.');
            await expect(reportsPage.generateReportFormSuccessContainer).not.toBeVisible();
        });

    });

    test('User can download an existing report from the reports history', async ({ page, api }) => {
        const reportsPage = new ReportsPage(page);

        await step('Create a test transaction for the report', async () => {

            await page.clock.setFixedTime(new Date('2026-05-30T12:00:00Z'));

            const cat_id = await api.categories.getCategoryIdByName('Entertainment');
            await api.transactions.createTransaction({
                amount: 150,
                transaction_type: 'expense',
                created_at: '2026-03-15T12:00:00Z',
                title: 'Test Transaction for Report History',
                category_id: cat_id,
            });
        });

        await step('Generate a report to ensure there is a report in the history', async () => {
            await reportsPage.goto();
            await reportsPage.reportStartDateInput.fill('2026-03-01');
            await reportsPage.reportEndDateInput.fill('2026-03-31');
            await reportsPage.generateReportButton.click();
            await page.waitForTimeout(3000);

        });
        
        await step('Download the report from the reports history and verify the file', async () => {
            await reportsPage.goto();

            const downloadPromise = page.waitForEvent('download');
            await reportsPage.downloadFirstReportByTable();

            const download = await downloadPromise;
            const fileName = download.suggestedFilename();
            expect(fileName).toMatch(/.*\.pdf$/);

            const downloadPath = path.join(test.info().outputDir, fileName);
            await download.saveAs(downloadPath);
            expect(fs.existsSync(downloadPath)).toBeTruthy();
            
            const stats = fs.statSync(downloadPath);
            expect(stats.size).toBeGreaterThan(1000);
        });

    });
});