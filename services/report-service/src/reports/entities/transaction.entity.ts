import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { Category } from './category.entity';

@Entity({ name: 'transactions', synchronize: false })
export class Transaction {
  @PrimaryGeneratedColumn()
  id!: number;

  @Column({ name: 'user_id' })
  userId!: number;

  @Column({ name: 'category_id' })
  categoryId!: number;

  @ManyToOne(() => Category)
  @JoinColumn({ name: 'category_id' })
  category!: Category;

  @Column({ name: 'amount', type: 'decimal', precision: 10, scale: 2 })
  amount!: number;

  @Column({ name: 'title' })
  title!: string;

  @Column({ name: 'created_at', type: 'timestamp' })
  date!: Date;

  @Column({ name: 'transaction_type' })
  type!: string; // income or expense, but in DB type=string

  get correctedAmount(): number {
    return this.type === 'expense' ? -Math.abs(this.amount) : this.amount;
  }
}
