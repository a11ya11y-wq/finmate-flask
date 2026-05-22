import {
  IsDateString,
  IsNotEmpty,
  IsInt,
  IsString,
  IsEmail,
  IsArray,
  ValidateNested,
  IsDecimal,
} from 'class-validator';
import { Type } from 'class-transformer';

class UserDTO {
  @IsString({ message: 'Username must be a string' })
  @IsNotEmpty({ message: 'Username is required' })
  username!: string;

  @IsNotEmpty({ message: 'Email is required' })
  @IsEmail({}, { message: 'Email must be a valid email address' })
  email!: string;
}

class TransactionDTO {
  @IsString({ message: 'Title must be a string' })
  @IsNotEmpty({ message: 'Title is required' })
  title!: string;

  @IsDateString({}, { message: 'Date must be a valid ISO 8601 date string' })
  @IsNotEmpty({ message: 'Date is required' })
  date!: string;

  @IsDecimal(
    { decimal_digits: '1,2' },
    {
      message:
        'Amount must be a valid decimal number with up to 2 decimal places',
    },
  )
  @IsNotEmpty({ message: 'Amount is required' })
  amount!: number;

  @IsString({ message: 'Category must be a string' })
  @IsNotEmpty({ message: 'Category is required' })
  category!: string;
}

export class ReportTaskPayload {
  @IsInt({ message: 'The report ID must be an integer' })
  @IsNotEmpty({ message: 'The report ID is required' })
  reportId!: number;

  @Type(() => UserDTO)
  @IsNotEmpty({ message: 'User information is required' })
  @ValidateNested()
  user!: UserDTO;

  @Type(() => TransactionDTO)
  @IsArray({ message: 'Transactions must be an array' })
  @IsNotEmpty({ message: 'Transactions are required' })
  @ValidateNested({ each: true })
  transactions!: TransactionDTO[];
}
