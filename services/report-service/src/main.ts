import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { Logger } from '@nestjs/common';

async function bootstrap() {
  const logger = new Logger('Bootstrap');

  const app = await NestFactory.createApplicationContext(AppModule);

  await app.init();
  logger.log('🚀 Report Worker Service is running and waiting for tasks... 🚀');
}

bootstrap().catch((err: unknown) => {
  if (err instanceof Error) {
    new Logger('Bootstrap').error(
      `Application failed to start: ${err.message}`,
    );
  }
});
