import { Controller, Inject, Logger } from '@nestjs/common';
import { EventPattern, Payload } from '@nestjs/microservices';
import { ReportsService } from './reports.service';
import { PdfService } from './pdf.service';
import { CreateReportDto } from './dto/create-report.dto';
import { ReportStatus } from './entities/report.entity';
import * as fs from 'node:fs';
import Redis from 'ioredis';

@Controller()
export class ReportsController {
  private readonly logger = new Logger(ReportsController.name);

  constructor(
    private readonly reportsService: ReportsService,
    private readonly pdfService: PdfService,

    @Inject('REDIS_CLIENT') private readonly redis: Redis,
  ) {}

  @EventPattern('reports_queue')
  async handleCreateReport(@Payload() data: CreateReportDto): Promise<void> {
    const reqId = data.requestId;
    const redisStatusKey = `request:${reqId}:status`;
    const redisFileKey = `request:${reqId}:file`;
    const redisErrorKey = `request:${reqId}:error`;

    let currentReportId: number = 0;

    try {
      const existingReport = await this.reportsService.findExistingReport(
        data.userId,
        new Date(data.startDate),
        new Date(data.endDate),
      );
      if (existingReport) {
        this.logger.log(
          `Found existing report ID: ${existingReport.id} for user ${data.userId} with status ${existingReport.status}`,
        );
      }

      if (existingReport?.status === ReportStatus.PENDING) {
        this.logger.log(
          `Report: ${existingReport.id} is still being pending. Linking request ID ${reqId}.`,
        );
        // Pending response when an existing report is still being processed
        await this.redis.set(redisStatusKey, ReportStatus.PENDING);
        return;
      }

      if (existingReport && existingReport.fileName) {
        const fullPath = `./uploads/${existingReport.fileName}`;
        if (fs.existsSync(fullPath)) {
          this.logger.log(`Returning existing report ID: ${existingReport.id}`);
          // Success response with existing file name
          await this.redis.set(redisFileKey, existingReport.fileName);
          await this.redis.set(redisStatusKey, ReportStatus.PROCESSED);
          return;
        }
      }
      const report = await this.reportsService.create(data);
      currentReportId = report.id;

      const transactions = await this.reportsService.getTransactionsForReport(
        report.userId,
        new Date(report.startDate),
        new Date(report.endDate),
      );

      if (!transactions || transactions.length === 0) {
        this.logger.warn(`No transactions found for report ID ${report.id}.`);
        await this.reportsService.updateReportStatus(
          report.id,
          ReportStatus.FAILED,
          null,
        );
        // Failure response when no transactions are found
        await this.redis.set(
          redisErrorKey,
          'No transactions found for the specified period.',
        );
        await this.redis.set(redisStatusKey, ReportStatus.FAILED);
        return;
      }

      const fileName = await this.pdfService.generateTxReport(
        report.id,
        transactions,
      );

      await this.reportsService.updateReportStatus(
        report.id,
        ReportStatus.PROCESSED,
        fileName,
      );
      this.logger.log(
        `Report ID ${report.id} for user ${report.userId} includes ${transactions.length} transactions`,
      );
      // Success response with file name
      await this.redis.set(redisFileKey, fileName);
      await this.redis.set(redisStatusKey, ReportStatus.PROCESSED);

      return;
    } catch (error) {
      this.logger.error(
        `Error processing report ID ${currentReportId}:`,
        error,
      );
      if (currentReportId !== 0) {
        await this.reportsService.updateReportStatus(
          currentReportId,
          ReportStatus.FAILED,
        );
      }
      // Failure response
      await this.redis.set(
        redisErrorKey,
        'An error occurred while processing the report.',
      );
      await this.redis.set(redisStatusKey, ReportStatus.FAILED);
      return;
    }
  }
}
