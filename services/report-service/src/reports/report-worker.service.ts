import { Injectable, OnModuleInit, Logger, Inject } from '@nestjs/common';
import { PdfService } from './pdf.service';
import { ReportTaskPayload } from './dto/report-task.dto';
import Redis from 'ioredis/built/Redis';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';

@Injectable()
export class ReportWorkerService implements OnModuleInit {
  private readonly logger = new Logger(ReportWorkerService.name);

  constructor(
    private readonly pdfService: PdfService,
    @Inject('REDIS_CLIENT') private readonly redis: Redis,
  ) {}

  onModuleInit() {
    this.logger.log(
      'ReportWorkerService initialized, starting to listen for report tasks...',
    );
    void this.listenForReportTasks(); // Start listening for tasks in the background
  }

  private async listenForReportTasks() {
    while (true) {
      try {
        const result = await this.redis.blpop('pdf_task_queue', 0); // Blocking Left Pop
        if (result) {
          const [, taskString] = result;
          await this.processTask(taskString);
        }
      } catch (err) {
        this.logger.error(
          'Error occurred while listening for report tasks:',
          err,
        );
        await new Promise((resolve) => setTimeout(resolve, 5000)); // Wait before retrying
      }
    }
  }

  private async processTask(taskString: string) {
    let parsedJson: unknown;

    try {
      parsedJson = JSON.parse(taskString) as unknown;
    } catch {
      this.logger.error(
        `FATAL: Failed to parse task JSON. Cannot notify Flask. Payload: ${taskString}`,
      );
      return;
    }

    if (typeof parsedJson !== 'object' || parsedJson === null) {
      this.logger.error(
        `FATAL: Payload is not a valid JSON object. Payload: ${taskString}`,
      );
      return;
    }

    const rawPayload = parsedJson as Record<string, unknown>;
    const rawReportId = rawPayload.reportId;

    if (typeof rawReportId !== 'number') {
      this.logger.error(
        'FATAL: Payload missing reportId or it is not a number. Cannot notify Flask.',
      );
      return;
    }

    const reportId: number = rawReportId;
    const redisResultKey = `report_result:${reportId}`;

    // Validate the payload
    try {
      const payload = plainToInstance(ReportTaskPayload, parsedJson);
      const errors = await validate(payload);
      if (errors.length > 0) {
        this.logger.error(`Validation failed for task payload:`, errors);
        // Store the error
        await this.redis.setex(
          redisResultKey,
          3600,
          JSON.stringify({
            status: 'error',
            message: 'Validation failed',
          }),
        );
        return;
      }

      const { reportId, transactions, closingBalance, openingBalance, user } =
        payload;
      this.logger.log(`Processing report task for report ID: ${reportId}`);

      const fileUrl = await this.pdfService.generateTxReport(
        reportId,
        transactions,
        closingBalance,
        openingBalance,
        user,
      );
      // Store the result with an expiration time
      await this.redis.setex(
        redisResultKey,
        3600,
        JSON.stringify({
          status: 'success',
          fileUrl: fileUrl,
        }),
      );
      this.logger.log(
        `Report generated successfully for report ID: ${reportId}, stored in Redis with key: ${redisResultKey}`,
      );
    } catch (err) {
      this.logger.error(
        `Failed to generate report for report ID: ${reportId}:`,
        err,
      );
      await this.redis.setex(
        redisResultKey,
        3600,
        JSON.stringify({
          status: 'error',
          message: 'Failed to generate report',
        }),
      );
    }
  }
}
