import { Injectable, Logger } from '@nestjs/common';
import { Report, ReportStatus } from './entities/report.entity';
import { InjectRepository } from '@nestjs/typeorm';
import { LessThan, Repository } from 'typeorm';
import { Cron, CronExpression } from '@nestjs/schedule';
import * as fs from 'node:fs';
import { ReportsService } from './reports.service';

@Injectable()
export class TasksService {
  private readonly logger = new Logger(TasksService.name);

  constructor(
    @InjectRepository(Report)
    private readonly reportsRepository: Repository<Report>,
    private readonly reportsService: ReportsService,
  ) {}

  @Cron(CronExpression.EVERY_HOUR)
  async handleReportCleanup() {
    this.logger.log('Running report cleanup task...');
    const expirationDate = new Date();
    expirationDate.setHours(expirationDate.getHours() - 24);

    const expiredReports = await this.reportsRepository.find({
      where: {
        status: ReportStatus.PROCESSED,
        createdAt: LessThan(expirationDate),
      },
    });

    for (const report of expiredReports) {
      if (report.filePath && fs.existsSync(report.filePath)) {
        try {
          fs.unlinkSync(report.filePath);
          this.logger.log(`Deleted file for expired report ID: ${report.id}`);
        } catch (error: unknown) {
          if (error instanceof Error) {
            this.logger.error(
              `Failed to delete file ${report.filePath}: ${error.message}`,
            );
          }
        }
      }
      try {
        await this.reportsService.updateReportStatus(
          report.id,
          ReportStatus.EXPIRED,
          null,
        );
      } catch (error: unknown) {
        if (error instanceof Error) {
          this.logger.error(
            `Failed to update status for report ID ${report.id}: ${error.message}`,
          );
        }
      }
    }
    this.logger.log(
      `Report cleanup completed. Expired reports processed: ${expiredReports.length}`,
    );
  }
}
