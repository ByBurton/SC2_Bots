import sc2;
from sc2 import Race;
from sc2.player import Bot;
import random;
from CarrierSpam import CarrierSpamBot;
from MutaliskBrood import MutaliskBrood;


def main(player1, player2, _map, realtime):
    sc2.run_game(sc2.maps.get(_map), [player1, player2], realtime=realtime);


if __name__ == "__main__":
    bot1 = sc2.player.Bot(sc2.Race.Protoss, CarrierSpamBot());
    bot2 = sc2.player.Bot(sc2.Race.Zerg, MutaliskBrood());

    # if you want to use the builtin bots
    # fixed race seems to use different strats than sc2.Race.Random
    race = random.choice([sc2.Race.Zerg, sc2.Race.Terran, sc2.Race.Protoss, sc2.Race.Random]);
    builtin_bot = sc2.player.Computer(race, sc2.Difficulty.CheatInsane);

    # random choice of map
    laddermaps = random.choice(
        [
        	"BelShirVestigeLE"
            #"AutomatonLE",
            #"BlueshiftLE",
            #"CeruleanFallLE",
            #"KairosJunctionLE",
            #"ParaSiteLE",
            #"PortAleksanderLE"#,
            # "StasisLE",
            # "DarknessSanctuaryLE"
        ]
    );
    # main(bot1, builtin_bot, laddermaps, realtime=False);
    # main(bot2, builtin_bot, laddermaps, realtime=False);
    main(bot1, bot2, laddermaps, realtime=False);
    # main(human, bot, laddermaps, realtime=True);
