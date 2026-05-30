import { test, expect } from '../fixtures/dynamicUserFixture';
import { ReportsPage } from '../pages/reports/ReporstPage';
import path from 'path';
import fs from 'fs';



test.describe('Reports Page', () => {

    test('User can generate a report for the last month using quick range selection', async ({ page }) => {
        
        await page.clock.setFixedTime(new Date('2026-05-30T12:00:00Z'));

        const reportsPage = new ReportsPage(page);
        await reportsPage.goto();

        await reportsPage.quickRangeMonthButton.click();
        await reportsPage.generateReportButton.click();

        await expect(reportsPage.generateReportFormSuccessContainer).toBeVisible({ timeout: 10000 });
        await expect(reportsPage.generateReportFormSuccessTitle).toHaveText('Report is ready');
        await expect(reportsPage.generateReportFormSuccessPeriod).toHaveText(/Period: May 01, 2026 - May 30, 2026/);

        const row = await reportsPage.getReportRowByIndex(0);
        await expect(row).toBeVisible();
        await expect(row).toContainText('May 30, 2026');
        await expect(row).toContainText('Processed');
        
        await expect(reportsPage.downloadReportButton).toBeVisible();

        const downloadPromise = page.waitForEvent('download');

        await reportsPage.downloadReportButton.click();

        const download = await downloadPromise;
        const fileName = download.suggestedFilename();
        expect(fileName).toMatch(/.*\.pdf$/);
        const downloadPath = path.join(test.info().outputDir, fileName);
        await download.saveAs(downloadPath);

        expect(fs.existsSync(downloadPath)).toBeTruthy();

        // 7. НАЙГОЛОВНІШЕ: перевіряємо, що файл не битий (не 0 байт)
        const stats = fs.statSync(downloadPath);
        
        // Нормальний PDF-звіт з транзакціями буде важити мінімум кілька кілобайт.
        // Перевіряємо, що він більший хоча б за 1000 байт (1 KB).
        expect(stats.size).toBeGreaterThan(1000);
    });
});
