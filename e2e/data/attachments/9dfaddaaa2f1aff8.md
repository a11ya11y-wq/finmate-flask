# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e/reports.spec.ts >> Reports Page >> User can generate a report for the last month using quick range selection
- Location: tests/e2e/reports.spec.ts:11:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForEvent: Test timeout of 30000ms exceeded.
=========================== logs ===========================
waiting for event "download"
============================================================
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - link "FinMate" [ref=e6] [cursor=pointer]:
        - /url: /dashboard
        - img "FinMate" [ref=e7]
      - button "Avatar usr_msc3rt0vq9uw2 " [ref=e9] [cursor=pointer]:
        - img "Avatar" [ref=e10]
        - generic [ref=e11]: usr_msc3rt0vq9uw2
        - generic [ref=e12]: 
  - main [ref=e13]:
    - generic [ref=e14]:
      - generic [ref=e15]:
        - generic [ref=e17]: 
        - generic [ref=e18]:
          - heading "Reports & Analytics" [level=2] [ref=e19]
          - paragraph [ref=e20]: Generate and download your financial statements.
      - generic [ref=e21]:
        - generic [ref=e22]:
          - generic [ref=e23]:
            - generic [ref=e26]:
              - generic [ref=e28]: 
              - generic [ref=e29]:
                - heading "Export data" [level=3] [ref=e30]
                - paragraph [ref=e31]: Generate a transaction report for your selected period.
            - generic [ref=e33]:
              - generic [ref=e34]:
                - generic [ref=e36]: 
                - generic [ref=e37]:
                  - paragraph [ref=e38]: Report is ready
                  - paragraph [ref=e39]: "Period: May 01, 2026 - May 30, 2026"
              - generic [ref=e40]:
                - button "Download PDF" [active] [ref=e41] [cursor=pointer]
                - button "Create new" [ref=e42] [cursor=pointer]
          - generic [ref=e43]:
            - heading "What's included?" [level=3] [ref=e45]
            - generic [ref=e46]:
              - generic [ref=e47]:
                - generic [ref=e49]: 
                - generic [ref=e50]:
                  - paragraph [ref=e51]: Header
                  - paragraph [ref=e52]: Official FinMate branding and report period.
              - generic [ref=e53]:
                - generic [ref=e55]: 
                - generic [ref=e56]:
                  - paragraph [ref=e57]: Transactions
                  - paragraph [ref=e58]: Detailed list of all incomes and expenses.
              - generic [ref=e59]:
                - generic [ref=e61]: 
                - generic [ref=e62]:
                  - paragraph [ref=e63]: Categories
                  - paragraph [ref=e64]: Smart tags for quick expense scanning.
              - generic [ref=e65]:
                - generic [ref=e67]: 
                - generic [ref=e68]:
                  - paragraph [ref=e69]: Summary
                  - paragraph [ref=e70]: Final closing balance and totals.
        - generic [ref=e71]:
          - generic [ref=e74]:
            - generic [ref=e76]: 
            - generic [ref=e77]:
              - heading "Recent reports" [level=3] [ref=e78]
              - paragraph [ref=e79]: View your latest exports and download links.
          - generic [ref=e82]:
            - generic [ref=e83]:
              - paragraph [ref=e84]: May 01, 2026 - May 30, 2026
              - generic [ref=e85]:
                - generic [ref=e86]: PROCESSED
                - generic [ref=e87]: Created 8/2/2026
            - button "Download" [ref=e89] [cursor=pointer]
```

# Test source

```ts
  1   | import { test, expect } from '../fixtures/dynamicUserFixture';
  2   | import { ReportsPage } from '../pages/reports/ReporstPage';
  3   | import { step } from 'allure-js-commons';
  4   | import path from 'path';
  5   | import fs from 'fs';
  6   | 
  7   | 
  8   | 
  9   | test.describe('Reports Page', () => {
  10  | 
  11  |     test('User can generate a report for the last month using quick range selection', async ({ page, api }) => {
  12  | 
  13  |         const reportsPage = new ReportsPage(page);
  14  | 
  15  |         await step('Create a transaction in the last month to ensure there is data for the report', async () => {
  16  | 
  17  |             const cat_id = await api.categories.getCategoryIdByName('Food');
  18  |             await api.transactions.createTransaction({
  19  |                 amount: 100,
  20  |                 transaction_type: 'income',
  21  |                 created_at: '2026-05-25T12:00:00Z',
  22  |                 title: 'Test Transaction for Report',
  23  |                 category_id: cat_id,
  24  |             });
  25  | 
  26  |             await page.clock.setFixedTime(new Date('2026-05-30T12:00:00Z'));
  27  |         });
  28  | 
  29  |         await step('Generate a report for the last month and verify the results', async () => {
  30  | 
  31  |             await reportsPage.goto();
  32  | 
  33  |             await reportsPage.quickRangeMonthButton.click();
  34  |             await reportsPage.generateReportButton.click();
  35  | 
  36  |             await expect(reportsPage.generateReportFormSuccessContainer).toBeVisible({ timeout: 30000 });
  37  |             await expect(reportsPage.generateReportFormSuccessTitle).toHaveText('Report is ready');
  38  |             await expect(reportsPage.generateReportFormSuccessPeriod).toHaveText(/Period: May 01, 2026 - May 30, 2026/);
  39  | 
  40  |             const row = await reportsPage.getFirstProcessedReportRow();
  41  |             await expect(row).toContainText('Processed', { ignoreCase: true });
  42  |             await expect(row).toContainText('May 30, 2026');
  43  |         });
  44  | 
  45  |         await step('Download the generated report and verify the file', async () => {
  46  |         
  47  |             await expect(reportsPage.downloadReportButton).toBeVisible();
  48  | 
> 49  |             const downloadPromise = page.waitForEvent('download');
      |                                          ^ Error: page.waitForEvent: Test timeout of 30000ms exceeded.
  50  | 
  51  |             await reportsPage.downloadReportButton.click();
  52  | 
  53  |             const download = await downloadPromise;
  54  |             const fileName = download.suggestedFilename();
  55  |             expect(fileName).toMatch(/.*\.pdf$/);
  56  |             const downloadPath = path.join(test.info().outputDir, fileName);
  57  |             await download.saveAs(downloadPath);
  58  | 
  59  |             expect(fs.existsSync(downloadPath)).toBeTruthy();
  60  |             const stats = fs.statSync(downloadPath);
  61  |             expect(stats.size).toBeGreaterThan(1000);
  62  |         });
  63  |     });
  64  | 
  65  |     test('User can generate a report for a custom date range', async ({ page, api }) => {
  66  | 
  67  |         const reportsPage = new ReportsPage(page);
  68  | 
  69  |         await step('Create transactions in the specified date range to ensure there is data for the report', async () => {
  70  | 
  71  |             const cat_id = await api.categories.getCategoryIdByName('Utilities');
  72  |             await api.transactions.createTransaction({
  73  |                 amount: 50,
  74  |                 transaction_type: 'expense',
  75  |                 created_at: '2026-04-10T12:00:00Z',
  76  |                 title: 'Test Transaction for Custom Report',
  77  |                 category_id: cat_id,
  78  |             });
  79  |             await api.transactions.createTransaction({
  80  |                 amount: 75,
  81  |                 transaction_type: 'expense',
  82  |                 created_at: '2026-04-20T12:00:00Z',
  83  |                 title: 'Another Test Transaction for Custom Report',
  84  |                 category_id: cat_id,
  85  |             });
  86  | 
  87  |             await page.clock.setFixedTime(new Date('2026-04-25T12:00:00Z'));
  88  | 
  89  |         });
  90  | 
  91  |         await step('Generate a report for the custom date range and verify the results', async () => {
  92  |             await reportsPage.goto();
  93  |             await reportsPage.reportStartDateInput.fill('2026-04-01');
  94  |             await reportsPage.reportEndDateInput.fill('2026-04-30');
  95  |             await reportsPage.generateReportButton.click();
  96  | 
  97  |             await expect(reportsPage.generateReportFormSuccessContainer).toBeVisible({ timeout: 30000 });
  98  |             await expect(reportsPage.generateReportFormSuccessTitle).toHaveText('Report is ready');
  99  |             await expect(reportsPage.generateReportFormSuccessPeriod).toHaveText(/Period: Apr 01, 2026 - Apr 30, 2026/);
  100 | 
  101 |             const row = await reportsPage.getFirstProcessedReportRow();
  102 |             await expect(row).toContainText('Processed', { ignoreCase: true });
  103 |             await expect(row).toContainText('Apr 01, 2026 - Apr 30, 2026');
  104 |         });
  105 | 
  106 |         await step('Download the generated report and verify the file', async () => {
  107 | 
  108 |             await expect(reportsPage.downloadReportButton).toBeVisible();
  109 |             const downloadPromise = page.waitForEvent('download');
  110 |             await reportsPage.downloadReportButton.click();
  111 | 
  112 |             const download = await downloadPromise;
  113 |             const fileName = download.suggestedFilename();
  114 |             expect(fileName).toMatch(/.*\.pdf$/);
  115 | 
  116 |             const downloadPath = path.join(test.info().outputDir, fileName);
  117 |             await download.saveAs(downloadPath);
  118 | 
  119 |             expect(fs.existsSync(downloadPath)).toBeTruthy();
  120 |             const stats = fs.statSync(downloadPath);
  121 |             expect(stats.size).toBeGreaterThan(1000);
  122 |         });
  123 | 
  124 |     });
  125 | 
  126 |     test('User cant generate a report without transactions in the selected period', async ({ page }) => {
  127 | 
  128 |         const reportsPage = new ReportsPage(page);
  129 | 
  130 |         await step('Generate a report for a period with no transactions and verify the error message', async () => {
  131 |             await reportsPage.goto();
  132 |             await reportsPage.reportStartDateInput.fill('2025-01-01');
  133 |             await reportsPage.reportEndDateInput.fill('2025-01-31');
  134 |             await reportsPage.generateReportButton.click();
  135 | 
  136 |             await reportsPage.toast.expectError('No transactions found for the specified period for report.');
  137 | 
  138 |             await expect(reportsPage.generateReportFormSuccessContainer).not.toBeVisible();
  139 |         });
  140 |     
  141 |     });
  142 | 
  143 |     test('User cannot generate a report with invalid date range', async ({ page }) => {
  144 | 
  145 |         const reportsPage = new ReportsPage(page);
  146 | 
  147 |         await step('Attempt to generate a report with an invalid date range and verify the error message', async () => {
  148 |             await reportsPage.goto();
  149 |             await reportsPage.reportStartDateInput.fill('2026-05-10');
```