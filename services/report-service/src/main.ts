import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import {
  MicroserviceOptions,
  RpcException,
  Transport,
} from '@nestjs/microservices';
import { Logger, ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  console.log('TEST ENV:', process.env.REPORT_SERVICE_DATABASE_URL);
  const app = await NestFactory.createMicroservice<MicroserviceOptions>(
    AppModule,
    {
      transport: Transport.REDIS,
      options: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379'),
      },
    },
  );

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      exceptionFactory: (validationErrors) => {
        const logger = new Logger('Validation');

        const messages = validationErrors.map((err) => {
          const constraints = err.constraints
            ? Object.values(err.constraints)
            : [];
          return `${err.property}: ${constraints.join(', ')}`;
        });

        logger.error(`Validation failed: ${messages.join('; ')}`);

        return new RpcException({
          status: 'error',
          message: 'Validation failed',
          errors: messages,
        });
      },
    }),
  );
  await app.listen();
  logger.log('🚀Report service is listening...🚀');
}
bootstrap().catch((err: unknown) => {
  if (err instanceof Error) {
    new Logger('Bootstrap').error(
      `Application failed to start: ${err.message}`,
    );
  }
});
