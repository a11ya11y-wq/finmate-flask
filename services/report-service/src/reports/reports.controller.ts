import { Controller, Logger } from '@nestjs/common';
import { MessagePattern, Payload } from '@nestjs/microservices';
import { ReportsService } from './reports.service';
import { PdfService } from './pdf.service';
import { CreateReportDto } from './dto/create-report.dto';
import { ReportStatus } from './entities/report.entity';
import * as fs from 'node:fs';

interface ReportResponse {
  reportId: number;
  fileName?: string;
  status?: ReportStatus;
  msg?: string;
}

@Controller()
export class ReportsController {
  private readonly logger = new Logger(ReportsController.name);

  constructor(
    private readonly reportsService: ReportsService,
    private readonly pdfService: PdfService,
  ) {}

  @MessagePattern('reports_queue')
  async handleCreateReport(
    @Payload() data: CreateReportDto,
  ): Promise<ReportResponse> {
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
          `The report: ${existingReport.id} is still being pending for user ${data.userId}`,
        );
        return {
          reportId: existingReport.id,
          status: ReportStatus.PROCESSED,
          msg: 'A report for the specified date range is currently being processed. Please check back later.',
        };
      }

      if (existingReport && existingReport.fileName) {
        const fullPath = `./uploads/${existingReport.fileName}`;
        if (fs.existsSync(fullPath)) {
          this.logger.log(`Returning existing report ID: ${existingReport.id}`);
          return {
            reportId: existingReport.id,
            fileName: existingReport.fileName,
            msg: 'A report for the specified date range already exists. Returning the existing report.',
          };
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
        return {
          reportId: report.id,
          status: ReportStatus.FAILED,
          msg: 'No transactions found for the specified date range. Report generation failed.',
        };
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

      return { reportId: report.id, fileName: fileName };
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
      return {
        reportId: currentReportId,
        status: ReportStatus.FAILED,
        msg: 'An error occurred while processing the report. Please try again later.',
      };
    }
  }
}
