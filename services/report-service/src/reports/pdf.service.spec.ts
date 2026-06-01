import { Test, TestingModule } from '@nestjs/testing';
import { PdfService } from './pdf.service';
import * as playwright from 'playwright';
import {
  jest,
  expect,
  describe,
  it,
  beforeEach,
  afterEach,
} from '@jest/globals';

// Fake environment variables for testing
process.env.DO_SPACES_ENDPOINT = 'https://fra1.digitaloceanspaces.com';
process.env.DO_SPACES_BUCKET = 'finmate-test-bucket';
process.env.DO_SPACES_REGION = 'fra1';
process.env.DO_SPACES_KEY = 'test-key';
process.env.DO_SPACES_SECRET = 'test-secret';

interface MockPlaywright {
  chromium: { launch: jest.Mock<() => Promise<unknown>> };
  _mockSetContent: jest.Mock<(html: string) => Promise<void>>;
  _mockPdf: jest.Mock<() => Promise<Buffer>>;
}

// Mocks Playwright
jest.mock('playwright', () => {
  const setContent = jest.fn<(html: string) => Promise<void>>(() =>
    Promise.resolve(),
  );
  const pdf = jest.fn<() => Promise<Buffer>>(() =>
    Promise.resolve(Buffer.from('fake pdf data')),
  );

  const mockPage = { setContent, pdf };

  const mockContext = {
    newPage: jest.fn(() => Promise.resolve(mockPage)),
    close: jest.fn(() => Promise.resolve()),
  };

  const mockBrowser = {
    newContext: jest.fn(() => Promise.resolve(mockContext)),
    close: jest.fn(() => Promise.resolve()),
  };

  return {
    chromium: {
      launch: jest.fn(() => Promise.resolve(mockBrowser)),
    },
    _mockSetContent: setContent,
    _mockPdf: pdf,
  };
});

// Mock AWS S3 Client
jest.mock('@aws-sdk/client-s3', () => {
  return {
    S3Client: jest.fn().mockImplementation(() => ({
      send: jest.fn(() => Promise.resolve()),
    })),
    PutObjectCommand: jest.fn(),
  };
});

describe('PdfService', () => {
  let service: PdfService;
  const pwMock = playwright as unknown as MockPlaywright;

  beforeEach(async () => {
    pwMock._mockSetContent.mockClear();
    pwMock._mockPdf.mockClear();

    const module: TestingModule = await Test.createTestingModule({
      providers: [PdfService],
    }).compile();

    service = module.get<PdfService>(PdfService);
    await service.onModuleInit();
  });

  afterEach(async () => {
    await service.onModuleDestroy();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should calculate correct balance for mixed transactions', async () => {
    const transactions = [
      {
        title: 'Income',
        date: '2026-05-01',
        amount: '150.00',
        category: 'Salary',
      },
      {
        title: 'Expense',
        date: '2026-05-02',
        amount: '-45.50',
        category: 'Food',
      },
    ];

    const resultUrl = await service.generateTxReport(1, transactions);

    expect(resultUrl).toMatch(
      /^https:\/\/fra1\.digitaloceanspaces\.com\/finmate-test-bucket\/report_1_.*\.pdf$/,
    );

    const generatedHtml = pwMock._mockSetContent.mock.calls[0][0];

    expect(generatedHtml).toContain('104.5');
    expect(generatedHtml).toContain('Income');
    expect(generatedHtml).toContain('Expense');
    expect(pwMock._mockPdf).toHaveBeenCalled();
  });

  it('should handle empty transactions array gracefully', async () => {
    const transactions: [] = [];

    const resultUrl = await service.generateTxReport(2, transactions);

    expect(resultUrl).toMatch(
      /^https:\/\/fra1\.digitaloceanspaces\.com\/finmate-test-bucket\/report_2_.*\.pdf$/,
    );

    const generatedHtml = pwMock._mockSetContent.mock.calls[0][0];

    expect(generatedHtml).toContain('0');
    expect(pwMock._mockPdf).toHaveBeenCalled();
  });

  it('should calculate correctly when there are only expenses (negative balance)', async () => {
    const transactions = [
      {
        title: 'Taxi',
        date: '2026-05-01',
        amount: '-10.00',
        category: 'Transport',
      },
      {
        title: 'Coffee',
        date: '2026-05-02',
        amount: '-5.25',
        category: 'Food',
      },
    ];

    const resultUrl = await service.generateTxReport(3, transactions);

    expect(resultUrl).toMatch(
      /^https:\/\/fra1\.digitaloceanspaces\.com\/finmate-test-bucket\/report_3_.*\.pdf$/,
    );

    const generatedHtml = pwMock._mockSetContent.mock.calls[0][0];

    expect(generatedHtml).toContain('-15.25');
    expect(pwMock._mockPdf).toHaveBeenCalled();
  });
});
