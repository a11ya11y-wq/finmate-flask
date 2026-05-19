import { Module } from '@nestjs/common';
import { ReportsModule } from './reports/reports.module';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ScheduleModule } from '@nestjs/schedule';

@Module({
  imports: [
    ScheduleModule.forRoot(),
    ConfigModule.forRoot({ isGlobal: true, envFilePath: '../../.env' }),
    ReportsModule,
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        url: String(config.get<string>('REPORT_SERVICE_DATABASE_URL')),
        autoLoadEntities: true,
        synchronize: true, //TODO: Disable in production
        logging: true,
      }),
    }),
  ],
})
export class AppModule {}
