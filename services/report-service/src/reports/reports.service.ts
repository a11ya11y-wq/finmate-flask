import { Injectable } from '@nestjs/common';
import { CreateReportDto } from './dto/create-report.dto';
import { UpdateReportDto } from './dto/update-report.dto';

@Injectable()
export class ReportsService {
  async create(createReportDto: CreateReportDto) {
    const {userId, startDate, endDate} = createReportDto;
    console.log(`🛠 Початок генерації звіту для користувача #${userId}`);
    console.log(`📅 Період: ${startDate} - ${endDate}`)

    return {
      status: 'processed',
      msg: 'Звіт успішно згенеровано',
      data: {
        userId,
        generatedAt: new Date().toISOString(),
      }
    };
  }

}
