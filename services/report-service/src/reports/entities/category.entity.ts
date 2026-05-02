import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity({ name: 'categories', synchronize: false })
export class Category {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'user_id' })
  userId: number;

  @Column({ name: 'name' })
  name: string;
}
