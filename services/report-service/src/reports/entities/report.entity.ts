import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
} from 'typeorm';

export enum ReportStatus {
  PENDING = 'pending',
  PROCESSED = 'processed',
  FAILED = 'failed',
  EXPIRED = 'expired',
}

@Entity('reports')
export class Report {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'user_id' })
  userId: number;

  @Column({ name: 'start_date', type: 'timestamp' })
  startDate: Date;

  @Column({ name: 'end_date', type: 'timestamp' })
  endDate: Date;

  @Column({ type: 'enum', enum: ReportStatus, default: ReportStatus.PENDING })
  status: ReportStatus;

  @Column({ name: 'file_path', type: 'varchar', nullable: true })
  filePath?: string | null;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}
