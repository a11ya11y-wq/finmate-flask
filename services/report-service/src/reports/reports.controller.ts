import { Controller, Logger } from '@nestjs/common';
import { MessagePattern, Payload } from '@nestjs/microservices';
import { ReportsService } from './reports.service';
import { PdfService } from './pdf.service';
import { CreateReportDto } from './dto/create-report.dto';
import { ReportStatus, Report } from './entities/report.entity';
import * as fs from 'node:fs';

@Controller()
export class ReportsController {
  private readonly logger = new Logger(ReportsController.name);

  constructor(
    private readonly reportsService: ReportsService,
    private readonly pdfService: PdfService,
  ) {}

  @MessagePattern('reports_queue')
  async handleCreateReport(@Payload() data: CreateReportDto) {
    const report = await this.reportsService.create(data);
    try {
      const existingReport = await this.reportsService.findExistingReport(
        report.userId,
        new Date(report.startDate),
        new Date(report.endDate),
      );
      if (existingReport && existingReport.filePath) {
        if (fs.existsSync(existingReport.filePath)) {
          this.logger.log(`Returning existing report ID: ${existingReport.id}`);
          return {
            reportId: existingReport.id,
            filePath: existingReport.filePath,
          };
        }
      }
      const transactions = await this.reportsService.getTransactionsForReport(
        report.userId,
        new Date(report.startDate),
        new Date(report.endDate),
      );

      const filePath = await this.pdfService.generateTxReport(
        report.id,
        transactions,
      );

      await this.reportsService.updateReportStatus(
        report.id,
        ReportStatus.PROCESSED,
        filePath,
      );
      this.logger.log(
        `Report ID ${report.id} for user ${report.userId} includes ${transactions.length} transactions`,
      );

      return { reportId: report.id, filePath: filePath };
    } catch (error) {
      this.logger.error(`Error processing report ID ${report.id}:`, error);
      await this.reportsService.updateReportStatus(
        report.id,
        ReportStatus.FAILED,
      );
    }
  }
}
