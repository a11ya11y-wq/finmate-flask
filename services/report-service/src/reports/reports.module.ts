import { Module } from '@nestjs/common';
import { ReportsService } from './reports.service';
import { ReportsController } from './reports.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Report } from './entities/report.entity';
import { Transaction } from './entities/transaction.entity';
import { Category } from './entities/category.entity';
import { PdfService } from './pdf.service';
import { TasksService } from './tasks.service';
import { Redis } from 'ioredis';
import { ConfigService } from '@nestjs/config';

@Module({
  imports: [TypeOrmModule.forFeature([Report, Transaction, Category])],
  controllers: [ReportsController],
  providers: [
    ReportsService,
    PdfService,
    TasksService,
    {
      // Redis client provider key-value
      provide: 'REDIS_CLIENT',
      inject: [ConfigService],
      useFactory: (config: ConfigService) => {
        const redisUrl =
          config.get<string>('REPORT_REDIS_URL') || 'redis://redis:6379/0';
        return new Redis(redisUrl);
      },
    },
  ],
})
export class ReportsModule {}
