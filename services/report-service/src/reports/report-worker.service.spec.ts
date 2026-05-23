import { Test, TestingModule } from '@nestjs/testing';
import { ReportWorkerService } from './report-worker.service';
import { PdfService } from './pdf.service';
import { Logger } from '@nestjs/common';
import {
  jest,
  expect,
  describe,
  it,
  beforeEach,
  afterEach,
} from '@jest/globals';

describe('ReportWorkerService', () => {
  let service: ReportWorkerService;
  let mockPdfService: { generateTxReport: jest.Mock };
  let mockRedis: { blpop: jest.Mock; setex: jest.Mock };

  beforeEach(async () => {
    mockPdfService = {
      generateTxReport: jest
        .fn()
        .mockResolvedValue('report_123_test.pdf' as never),
    };

    mockRedis = {
      blpop: jest.fn().mockResolvedValue(null as never),
      setex: jest.fn().mockResolvedValue('OK' as never),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ReportWorkerService,
        {
          provide: PdfService,
          useValue: mockPdfService,
        },
        {
          provide: 'REDIS_CLIENT',
          useValue: mockRedis,
        },
      ],
    }).compile();

    service = module.get<ReportWorkerService>(ReportWorkerService);

    jest.spyOn(Logger.prototype, 'error').mockImplementation(() => {});
    jest.spyOn(Logger.prototype, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('processTask (Business Logic)', () => {
    it('should generate PDF and set success status in Redis', async () => {
      const validPayload = JSON.stringify({
        reportId: 123,
        user: {
          username: 'testuser',
          email: 'testuser@example.com',
        },
        transactions: [
          {
            title: 'Test',
            date: '2026-05-20',
            amount: '10.0',
            category: 'Food',
          },
        ],
      });

      await service['processTask'](validPayload);

      expect(mockPdfService.generateTxReport).toHaveBeenCalledWith(123, [
        { title: 'Test', date: '2026-05-20', amount: '10.0', category: 'Food' },
      ]);

      expect(mockRedis.setex).toHaveBeenCalledWith(
        'report_result:123',
        3600,
        JSON.stringify({ status: 'success', fileName: 'report_123_test.pdf' }),
      );
    });

    it('should silently drop task if JSON is invalid', async () => {
      const invalidJson = '{ broken json }';
      await service['processTask'](invalidJson);

      expect(mockPdfService.generateTxReport).not.toHaveBeenCalled();
      expect(mockRedis.setex).not.toHaveBeenCalled();
    });

    it('should drop task if reportId is missing or invalid', async () => {
      const noIdPayload = JSON.stringify({ transactions: [] });
      await service['processTask'](noIdPayload);

      expect(mockPdfService.generateTxReport).not.toHaveBeenCalled();
      expect(mockRedis.setex).not.toHaveBeenCalled();
    });

    it('should set error in Redis if payload validation fails', async () => {
      const invalidDtoPayload = JSON.stringify({
        reportId: 999,
        user: {
          username: 'testuser',
          email: 'testuser@example.com',
        },
        transactions: [
          { title: 'Test', date: '2026-05-20', amount: 100, category: 'Food' },
        ],
      });

      await service['processTask'](invalidDtoPayload);

      expect(mockPdfService.generateTxReport).not.toHaveBeenCalled();
      expect(mockRedis.setex).toHaveBeenCalledWith(
        'report_result:999',
        3600,
        JSON.stringify({ status: 'error', message: 'Validation failed' }),
      );
    });

    it('should set error in Redis if PdfService throws an exception', async () => {
      mockPdfService.generateTxReport.mockRejectedValueOnce(
        new Error('Browser crashed') as never,
      );

      const validPayload = JSON.stringify({
        reportId: 555,
        user: {
          username: 'testuser',
          email: 'testuser@example.com',
        },
        transactions: [
          {
            title: 'Test',
            date: '2026-05-20',
            amount: '10.0',
            category: 'Food',
          },
        ],
      });

      await service['processTask'](validPayload);

      expect(mockRedis.setex).toHaveBeenCalledWith(
        'report_result:555',
        3600,
        JSON.stringify({
          status: 'error',
          message: 'Failed to generate report',
        }),
      );
    });
  });
});
