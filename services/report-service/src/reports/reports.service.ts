import { Injectable, Logger } from '@nestjs/common';
import { CreateReportDto } from './dto/create-report.dto';
import { InjectRepository } from '@nestjs/typeorm';
import { Report, ReportStatus } from './entities/report.entity';
import { Between, Repository } from 'typeorm';
import { Transaction } from './entities/transaction.entity';

@Injectable()
export class ReportsService {
  private readonly logger = new Logger(ReportsService.name);

  constructor(
    @InjectRepository(Report)
    private readonly reportRepository: Repository<Report>,

    @InjectRepository(Transaction)
    private readonly transactionRepository: Repository<Transaction>,
  ) {}

  async create(dto: CreateReportDto) {
    const newReport = this.reportRepository.create({
      userId: dto.userId,
      startDate: dto.startDate,
      endDate: dto.endDate,
      status: ReportStatus.PENDING,
    });

    const savedReport = await this.reportRepository.save(newReport);
    this.logger.log(
      `Report created with ID: ${savedReport.id} for user ${savedReport.userId}`,
    );
    return savedReport;
  }

  async getTransactionsForReport(
    userId: number,
    startDate: Date,
    endDate: Date,
  ) {
    return await this.transactionRepository.find({
      where: {
        userId: userId,
        date: Between(startDate, endDate),
      },
      relations: ['category'],
      order: { date: 'ASC' },
    });
  }

  async updateReportStatus(
    reportId: number,
    status: ReportStatus,
    fileName?: string | null,
  ) {
    const report = await this.reportRepository.findOne({
      where: { id: reportId },
    });
    if (!report) {
      throw new Error(`Report with ID ${reportId} not found`);
    }
    report.status = status;
    report.fileName = fileName;
    await this.reportRepository.save(report);
    this.logger.log(`Report ID ${reportId} status updated to ${status}`);
  }

  async findExistingReport(userId: number, startDate: Date, endDate: Date) {
    return await this.reportRepository.findOne({
      where: {
        userId,
        startDate,
        endDate,
        status: ReportStatus.PROCESSED, // We need only completed reports
      },
    });
  }
}
