import {Page, Locator, expect } from '@playwright/test';
import { BasePage } from '../common/BasePage';
import { Header } from '../common/components/Header';
import { Toast } from '../common/components/Toast';


export class ReportsPage extends BasePage {
    protected readonly url = '/reports';

    // Export Data - Form
    readonly generateReportForm: Locator;

    readonly reportQuickPeriodContainer: Locator;
    readonly quickRangeMonthButton: Locator;
    readonly quickRangeYearButton: Locator
    readonly quickRangeAllButton: Locator;

    readonly reportStartDateInput: Locator;
    readonly reportEndDateInput: Locator;

    readonly generateReportButton: Locator;

    // Success State For Export Data
    readonly generateReportFormSuccessContainer: Locator

    readonly generateReportFormSuccessTitle: Locator;
    readonly generateReportFormSuccessPeriod: Locator;

    readonly downloadReportButton: Locator;
    readonly createNewReportButton: Locator;

    // Reports Table
    readonly reportsTable: Locator


    constructor(page: Page) {
        super(page);

        this.generateReportForm = this.page.getByTestId('generate-report-form');
        
        this.reportQuickPeriodContainer = this.generateReportForm.getByTestId('report-quick-period-container');
        this.quickRangeMonthButton = this.reportQuickPeriodContainer.getByTestId('quick-range-month');
        this.quickRangeYearButton = this.reportQuickPeriodContainer.getByTestId('quick-range-year');
        this.quickRangeAllButton = this.reportQuickPeriodContainer.getByTestId('quick-range-all');

        this.reportStartDateInput = this.generateReportForm.getByTestId('report-start-date-input');
        this.reportEndDateInput = this.generateReportForm.getByTestId('report-end-date-input');
        
        this.generateReportButton = this.generateReportForm.getByTestId('generate-report-button');
        
        
        this.generateReportFormSuccessContainer = this.page.getByTestId('generate-report-form-success');
        
        this.generateReportFormSuccessTitle = this.generateReportFormSuccessContainer.getByTestId('generate-report-form-success-title');
        this.generateReportFormSuccessPeriod = this.generateReportFormSuccessContainer.getByTestId('generate-report-form-success-period');
        
        this.downloadReportButton = this.generateReportFormSuccessContainer.getByTestId('download-report-button');
        this.createNewReportButton = this.generateReportFormSuccessContainer.getByTestId('create-new-report-button');


        this.reportsTable = this.page.getByTestId('reports-table');
    }

    async getFirstProcessedReportRow(): Promise<Locator> {
        const row = this.reportsTable.locator('div, button').filter({ hasText: 'Processed' }).first();
        return row;
    }

    async downloadFirstReportByTable(): Promise<void> {
        const row = await this.getFirstProcessedReportRow();
        const downloadButton = row.getByRole('button', { name: 'Download' });
        await expect(downloadButton).toBeVisible({ timeout: 25000 });
        await downloadButton.click();
    }
}