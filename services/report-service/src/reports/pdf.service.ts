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
import { ReportTaskPayload } from './dto/report-task.dto';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

@Injectable()
export class PdfService implements OnModuleInit, OnModuleDestroy {
  private browser!: Browser;
  private readonly logger = new Logger(PdfService.name);
  private readonly s3: S3Client;

  constructor() {
    this.s3 = new S3Client({
      endpoint: process.env.CLOUDFLARE_R2_ENDPOINT,
      region: process.env.CLOUDFLARE_R2_REGION || 'auto',
      forcePathStyle: true,
      credentials: {
        accessKeyId: process.env.CLOUDFLARE_R2_KEY!,
        secretAccessKey: process.env.CLOUDFLARE_R2_SECRET!,
      },
    });
  }

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

  async generateTxReport(
    reportId: number,
    transactions: ReportTaskPayload['transactions'],
    closingBalance: string,
    openingBalance: string,
    user: ReportTaskPayload['user'],
  ): Promise<string> {
    const templatePath = path.join(process.cwd(), 'templates', 'report.hbs');
    const templateHtml = fs.readFileSync(templatePath, 'utf-8');
    const template = Handlebars.compile(templateHtml);

    let totalIncome = 0;
    let totalExpenses = 0;

    const sortedTransactions = [...transactions].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    );

    let runningBalance = Number(openingBalance);

    const formattedTransactions = sortedTransactions.map((t) => {
      const amountNum = Number(t.amount);
      const isExpense = amountNum < 0;

      if (isExpense) {
        totalExpenses += Math.abs(amountNum);
      } else {
        totalIncome += amountNum;
      }

      runningBalance += amountNum;

      return {
        ...t,
        dateFormatted: new Date(t.date).toLocaleDateString('en-GB'),
        amountFormatted: Math.abs(amountNum).toFixed(2),
        balanceFormatted: runningBalance.toFixed(2),
        isExpense,
      };
    });

    const netCashFlow = totalIncome - totalExpenses;

    const htmlContent = template({
      reportId,
      currentDate: new Date().toLocaleDateString('en-GB'),
      openingBalance: Number(openingBalance).toFixed(2),
      closingBalance: Number(closingBalance).toFixed(2),
      totalIncome: totalIncome.toFixed(2),
      totalExpenses: totalExpenses.toFixed(2),
      netCashFlow: (netCashFlow >= 0 ? '+' : '') + netCashFlow.toFixed(2),
      isNetFlowPositive: netCashFlow >= 0,
      user,
      transactions: formattedTransactions.reverse(),
    });

    const context = await this.browser.newContext();

    try {
      const page = await context.newPage();
      await page.setContent(htmlContent, { waitUntil: 'networkidle' });

      const fileName = `report_${reportId}_${Date.now()}.pdf`;

      const pdfBuffer = await page.pdf({ format: 'A4', printBackground: true });

      const command = new PutObjectCommand({
        Bucket: process.env.CLOUDFLARE_R2_BUCKET,
        Key: fileName,
        Body: pdfBuffer,
        ContentType: 'application/pdf',
      });

      await this.s3.send(command);
      this.logger.log(
        `File ${fileName} successfully uploaded to CLOUDFLARE_R2`,
      );

      return fileName; // fileKey
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
