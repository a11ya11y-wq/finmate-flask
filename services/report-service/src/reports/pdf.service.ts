import {
  Injectable,
  Logger,
  OnModuleInit,
  OnModuleDestroy,
} from '@nestjs/common';
import { Browser, chromium } from 'playwright';
import path from 'node:path';
import * as fs from 'node:fs';
import * as Handlebars from 'handlebars';
import { Transaction } from './entities/transaction.entity';

@Injectable()
export class PdfService implements OnModuleInit, OnModuleDestroy {
  private browser!: Browser;
  private readonly logger = new Logger(PdfService.name);

  async onModuleInit() {
    this.logger.log('Launching playwright browser for PDF generation...');
    this.browser = await chromium.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
      ],
    });
    this.logger.log('Playwright browser launched successfully.');
  }

  async onModuleDestroy() {
    this.logger.log('Closing playwright browser...');
    if (this.browser) {
      await this.browser.close();
      this.logger.log('Playwright browser closed successfully.');
    } else {
      this.logger.warn('Playwright browser was not initialized.');
    }
  }

  async generateTxReport(reportId: number, transactions: Transaction[]) {
    const templatePath = path.join(process.cwd(), 'templates', 'report.hbs');
    const templateHtml = fs.readFileSync(templatePath, 'utf-8');

    const template = Handlebars.compile(templateHtml);

    const totalBalance = transactions.reduce((acc, t) => {
      return acc + Number(t.correctedAmount);
    }, 0);

    const htmlContent = template({
      reportId,
      currentDate: new Date().toLocaleDateString('en-GB'),
      totalBalance: totalBalance.toFixed(2),
      transactions: transactions.map((t) => ({
        ...t,
        dateFormatted: new Date(t.date).toLocaleDateString('en-GB'),
        amountFormatted: Math.abs(Number(t.correctedAmount)).toFixed(2),
        isExpense: Number(t.correctedAmount) < 0,
      })),
    });

    const context = await this.browser.newContext();

    try {
      const page = await context.newPage();
      await page.setContent(htmlContent, { waitUntil: 'networkidle' });

      const fileName = `report_${reportId}_${Date.now()}.pdf`;
      const REPORTS_UPLOAD_DIR = '/app/uploads'; // TODO: move to config!!!!
      const filePath = path.join(REPORTS_UPLOAD_DIR, fileName);

      await page.pdf({ path: filePath, format: 'A4', printBackground: true });

      return fileName;
    } catch (error) {
      this.logger.error(
        `Failed to generate PDF report: ${error instanceof Error ? error.message : error}`,
      );
      throw error;
    } finally {
      await context.close();
    }
  }
}
