import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ReportsModule } from './reports/reports.module';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [
      ConfigModule.forRoot({ isGlobal: true }),
      ReportsModule
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
