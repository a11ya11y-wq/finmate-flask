import { Module } from '@nestjs/common';
import { PdfService } from './pdf.service';
import { Redis } from 'ioredis';
import { ConfigService } from '@nestjs/config';
import { ReportWorkerService } from './report-worker.service';

@Module({
  imports: [],
  controllers: [],
  providers: [
    PdfService,
    ReportWorkerService,
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
