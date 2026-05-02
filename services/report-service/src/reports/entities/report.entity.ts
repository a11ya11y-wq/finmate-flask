import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
} from 'typeorm';

@Entity('reports')
export class Report {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'user_id' })
  userId: number;

  @Column({ name: 'start_date', type: 'timestamp' })
  startDate: string;

  @Column({ name: 'end_date', type: 'timestamp' })
  endDate: string;

  @Column({ type: 'varchar', length: 20 })
  status: 'pending' | 'processed' | 'failed';

  @Column({ name: 'file_path', nullable: true })
  filePath: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: string;
}
