import { BaseEntity, Entity, ManyToOne, PrimaryGeneratedColumn } from "typeorm";
import { DiscordUser } from "./MatchParticipant";

@Entity()
export class PastMatch extends BaseEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @ManyToOne(() => DiscordUser)
  personA: DiscordUser;

  @ManyToOne(() => DiscordUser)
  personB: DiscordUser;
}
