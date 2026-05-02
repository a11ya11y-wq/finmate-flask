import { Injectable } from '@nestjs/common';
import { CreateReportDto } from './dto/create-report.dto';
import { InjectRepository } from '@nestjs/typeorm';
import { Report } from './entities/report.entity';
import { Between, Repository } from 'typeorm';
import { Transaction } from './entities/transaction.entity';

@Injectable()
export class ReportsService {
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
      status: 'pending',
    });

    const savedReport = await this.reportRepository.save(newReport);
    console.log(
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
}
