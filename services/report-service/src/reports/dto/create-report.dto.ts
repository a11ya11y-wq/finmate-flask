import { IsDateString, IsNotEmpty, IsInt, IsString } from 'class-validator';

export class CreateReportDto {
  @IsString({ message: 'The request ID must be a string' })
  @IsNotEmpty({ message: 'The request ID is required' })
  requestId!: string; // UUID

  @IsInt({ message: 'The user ID must be a number' })
  @IsNotEmpty({ message: 'The user ID is required' })
  userId!: number;

  @IsDateString(
    {},
    { message: 'The start date must be a valid ISO 8601 date string' },
  )
  @IsNotEmpty({ message: 'The start date is required' })
  startDate!: string;

  // TODO: Add custom deco to compare startDate and endDate
  @IsDateString(
    {},
    { message: 'The end date must be a valid ISO 8601 date string' },
  )
  @IsNotEmpty({ message: 'The end date is required' })
  endDate!: string;
}
