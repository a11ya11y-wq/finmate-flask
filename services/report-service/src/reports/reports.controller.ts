import { Controller } from '@nestjs/common';
import { MessagePattern, Payload } from '@nestjs/microservices';
import { ReportsService } from './reports.service';
import { CreateReportDto } from './dto/create-report.dto';

@Controller()
export class ReportsController {
  constructor(private readonly reportsService: ReportsService) {}

  @MessagePattern('reports_queue')
  async handleCreateReport(@Payload() data: CreateReportDto) {
    const report = await this.reportsService.create(data);

    const transactions = await this.reportsService.getTransactionsForReport(
      report.userId,
      new Date(report.startDate),
      new Date(report.endDate),
    );

    console.log(
      `Report ID ${report.id} for user ${report.userId} includes ${transactions.length} transactions`,
    );

    return report;
  }
}
