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
      endpoint: process.env.DO_SPACES_ENDPOINT,
      region: process.env.DO_SPACES_REGION || 'us-east-1',
      credentials: {
        accessKeyId: process.env.DO_SPACES_KEY!,
        secretAccessKey: process.env.DO_SPACES_SECRET!,
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
  ): Promise<string> {
    const templatePath = path.join(process.cwd(), 'templates', 'report.hbs');
    const templateHtml = fs.readFileSync(templatePath, 'utf-8');

    const template = Handlebars.compile(templateHtml);

    const totalBalance = transactions.reduce((acc, t) => {
      return acc + Number(t.amount);
    }, 0);

    const htmlContent = template({
      reportId,
      currentDate: new Date().toLocaleDateString('en-GB'),
      totalBalance: totalBalance.toFixed(2),
      transactions: transactions.map((t) => ({
        ...t,
        dateFormatted: new Date(t.date).toLocaleDateString('en-GB'),
        amountFormatted: Math.abs(Number(t.amount)).toFixed(2),
        isExpense: Number(t.amount) < 0,
      })),
    });

    const context = await this.browser.newContext();

    try {
      const page = await context.newPage();
      await page.setContent(htmlContent, { waitUntil: 'networkidle' });

      const fileName = `report_${reportId}_${Date.now()}.pdf`;

      const pdfBuffer = await page.pdf({ format: 'A4' });

      const command = new PutObjectCommand({
        Bucket: process.env.DO_SPACES_BUCKET,
        Key: fileName,
        Body: pdfBuffer,
        ACL: 'public-read',
        ContentType: 'application/pdf',
      });

      await this.s3.send(command);
      this.logger.log(`File ${fileName} successfully uploaded to DO Spaces`);

      return `${process.env.DO_SPACES_ENDPOINT}/${process.env.DO_SPACES_BUCKET}/${fileName}`;
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
