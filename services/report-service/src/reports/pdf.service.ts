import { Injectable, Logger } from '@nestjs/common';
import puppeteer from 'puppeteer';
import path from 'node:path';
import * as fs from 'node:fs';
import * as Handlebars from 'handlebars';
import { Transaction } from './entities/transaction.entity';

@Injectable()
export class PdfService {
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

    const browser = await puppeteer.launch({
      headless: true,
      executablePath:
        process.env.PUPPETEER_EXECUTABLE_PATH || '/usr/bin/chromium-browser',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--headless',
      ],
    });
    try {
      const page = await browser.newPage();

      await page.setContent(htmlContent);

      const fileName = `report_${reportId}_${Date.now()}.pdf`;

      const REPORTS_UPLOAD_DIR = '/app/uploads'; // TODO: move to config!!!!
      const filePath = path.join(REPORTS_UPLOAD_DIR, fileName);

      await page.pdf({ path: filePath, format: 'A4', printBackground: true });
      await browser.close();
      return fileName;
    } catch (error) {
      Logger.error(
        `Failed to generate PDF report: ${error instanceof Error ? error.message : error}`,
      );
      throw error;
    } finally {
      await browser.close();
    }
  }
}
