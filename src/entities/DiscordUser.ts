import { BaseEntity, Column, Entity, PrimaryGeneratedColumn } from "typeorm";

@Entity()
export class DiscordUser extends BaseEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  discordId: string;

  @Column()
  signedUpToMatch: boolean;
}
