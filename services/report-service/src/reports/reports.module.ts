import { Module } from '@nestjs/common';
import { ReportsService } from './reports.service';
import { ReportsController } from './reports.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Report } from './entities/report.entity';
import { Transaction } from './entities/transaction.entity';
import { Category } from './entities/category.entity';
import { PdfService } from './pdf.service';
import { TasksService } from './tasks.service';

@Module({
  imports: [TypeOrmModule.forFeature([Report, Transaction, Category])],
  controllers: [ReportsController],
  providers: [ReportsService, PdfService, TasksService],
})
export class ReportsModule {}
