import sc2;
import random;

from sc2 import run_game, maps, Race, Difficulty;
from sc2.player import Bot, Computer, Human;
from sc2.constants import *;
from sc2.data import race_townhalls;

class ZealotTribe(sc2.BotAI):
	#def __init__(self):


	async def on_step(self, iteration):
		if round(self.time) % 3 == 0:
			await self.do_defend();

		if round(self.time) % 6 == 0:
			await self.distribute_workers();  # in sc2/bot_ai.py	
			await self.do_attack();	

		if round(self.time) % 9 == 0:
			await self.build_static_defenses();

		await self.build_pylons();
		await self.expand();
		await self.train_probes();
		await self.build_assimilators();
		await self.build_gate_ways();
		await self.build_cybernetics_core();
		await self.do_twilight_council_research();
		await self.build_forges();
		await self.build_twilight_council();
		await self.do_forge_research();
		await self.train_zealots();


	#try to upgrade an ability; checks if the structure has the ability to research tech.
	async def try_upgrade(self, facility, upgrade_id, ability_id):
		#not self.already_pending(upgrade_id) 
		if self.can_afford(upgrade_id) and not upgrade_id in self.state.upgrades:
			if await self.has_ability(ability_id, facility):
				await self.do(facility(ability_id));


	# Check if a unit has an ability available (also checks upgrade costs??)
	async def has_ability(self, ability, unit):
		abilities = await self.get_available_abilities(unit);
		if ability in abilities:
			return True;
		else:
			return False;


	def is_enemy_near(self):
		for building in self.units():
			bl_pos = building.position;
			if self.known_enemy_units.closer_than(22, bl_pos).exists:
				return True;
			else:
				return False;

	async def build_twilight_council(self):	
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if not self.units(CYBERNETICSCORE).ready.exists:
			return;

		if self.units(TWILIGHTCOUNCIL).ready.amount == 0 and self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
			await self.build(TWILIGHTCOUNCIL, near=pylon);

	async def train_zealots(self):
		if not self.units(GATEWAY).ready.exists:
			return;

		if self.minerals > 400 and not self.is_enemy_near():
			return;

		#prio to upgrades
		if not PROTOSSSHIELDSLEVEL3 in self.state.upgrades:
			if self.units(FORGE).ready.idle.exists:
				return;
		elif not PROTOSSGROUNDWEAPONSLEVEL3 in self.state.upgrades:
			if self.units(FORGE).ready.idle.exists:
				return;
		elif not PROTOSSGROUNDARMORSLEVEL3 in self.state.upgrades:
			if self.units(FORGE).ready.idle.exists:
				return;

		for gw in self.units(GATEWAY).ready.idle:
			if self.can_afford(ZEALOT) and self.supply_left >= 2:
				await self.do(gw.train(ZEALOT));

	async def build_static_defenses(self):
		if self.minerals < 2000 or not self.units(FORGE).ready.exists:
			return;

		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if not self.units(FORGE).ready.exists:
			return;

		#build a cannon and battery (3 times as many cannons)
		if self.can_afford(PHOTONCANNON):
			await self.build(PHOTONCANNON, near=pylon.position.towards(self.game_info.map_center, 4));
			if self.can_afford(SHIELDBATTERY) and self.units(SHIELDBATTERY).amount <= self.units(PHOTONCANNON).amount / 3:
				await self.build(SHIELDBATTERY, near=pylon.position.towards(self.game_info.map_center, -2));

	async def do_forge_research(self):
		forges = self.units(FORGE).ready.idle;
		if not forges.exists:
			return;

		if forges.exists:
			for forge in forges:
				await self.try_upgrade(forge, PROTOSSSHIELDSLEVEL1, AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1);
				await self.try_upgrade(forge, PROTOSSSHIELDSLEVEL2, AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2);
				await self.try_upgrade(forge, PROTOSSSHIELDSLEVEL3, AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3);

				await self.try_upgrade(forge, PROTOSSGROUNDWEAPONSLEVEL1, AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1);
				await self.try_upgrade(forge, PROTOSSGROUNDWEAPONSLEVEL2, AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2);
				await self.try_upgrade(forge, PROTOSSGROUNDWEAPONSLEVEL3, AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3);

				await self.try_upgrade(forge, PROTOSSGROUNDARMORSLEVEL1, AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1);
				await self.try_upgrade(forge, PROTOSSGROUNDARMORSLEVEL2, AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2);
				await self.try_upgrade(forge, PROTOSSGROUNDARMORSLEVEL3, AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3);

	async def do_twilight_council_research(self):
		tcs = self.units(TWILIGHTCOUNCIL).ready.idle;
		if not tcs.exists:
			return;

		if tcs.exists:
			for tc in tcs:
				await self.try_upgrade(tc, CHARGE, AbilityId.RESEARCH_CHARGE);

	async def expand(self):
		if self.can_afford(NEXUS) and self.units(PROBE).ready.amount > 10 * self.townhalls.amount and not self.already_pending(NEXUS):
			await self.expand_now();

	async def build_assimilators(self):
		for nexus in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(8, nexus);
			for vg in vgs:
				if not self.can_afford(ASSIMILATOR) or self.units(PROBE).amount <= 13:
					break;
				worker = self.select_build_worker(vg.position);
				if worker is None:
					break;
				if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
					await self.do(worker.build(ASSIMILATOR, vg));


	async def train_probes(self):
		if self.units(PROBE).amount >= 66:
			return;

		maxprobes = ( self.townhalls.ready.amount * 21 )
		if maxprobes >= 66:
			maxprobes = 66;

		nexi = self.townhalls.ready.idle;
		if nexi.exists:
			for nexus in nexi:
				if self.can_afford(PROBE) and self.supply_left >= 1 and self.units(PROBE).amount <= maxprobes:
					await self.do(nexus.train(PROBE));


	def find_target(self, state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units).position;
		elif len(self.known_enemy_structures):
			return random.choice(self.known_enemy_structures).position;
		else:
			return self.enemy_start_locations[0];


	async def build_pylons(self):
		nexi = self.townhalls.ready;
		if not nexi.exists:
			return;
		nexus = nexi.random;

		supply_no = 2 * self.units(GATEWAY).ready.amount + 1;
		if supply_no == 0:
			supply_no = 6;

		if self.units(PYLON).ready.amount >= 45:
			return;

		if self.supply_left <= supply_no and not self.already_pending(PYLON):
			if self.can_afford(PYLON):
				await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 10));
			return;

	async def build_gate_ways(self):
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if self.units(GATEWAY).ready.amount < 3 * self.townhalls.amount and self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
			await self.build(GATEWAY, near=pylon);

	async def build_forges(self):
		if self.townhalls.ready.amount <= 2:
			return;

		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if self.units(FORGE).ready.amount < 3 and self.can_afford(FORGE) and not self.already_pending(FORGE):
			await self.build(FORGE, near=pylon);


	async def build_cybernetics_core(self):
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if not self.units(GATEWAY).ready.exists:
			return;

		if self.units(CYBERNETICSCORE).ready.amount < 1 and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
			await self.build(CYBERNETICSCORE, near=pylon);


	async def do_attack(self):
		zealots = self.units(ZEALOT).idle;

		no_attackers = (self.units(GATEWAY).ready.amount * 2) + 5; #attack with at least 6 zealots
		
		if zealots.exists:
			if zealots.amount >= no_attackers:
				for zealot in zealots:
					await self.do(zealot.attack(self.find_target(self.state)));


	#todo: do not follow the enemy back to their base
	async def do_defend(self):
		zealots = self.units(ZEALOT).idle;

		for unit in self.units():
			unit_pos = unit.position;
			for zealot in zealots:
				if self.known_enemy_units.closer_than(20, unit_pos).exists:

					#print("defend: idle units: %d; total units: %d" % (forces.amount, nonidle.amount))

					choice = random.choice(self.known_enemy_units.closer_than(20, unit_pos));
					await self.do(zealot.attack(choice.position));
				else:
					break;





#runs the actual game
#run_game(maps.get("AbyssalReefLE"), [
run_game(maps.get("AbyssalReefLE"), [
	#Human(Race.Zerg),
	Bot(Race.Protoss, ZealotTribe()),
	Computer(Race.Protoss, Difficulty.Medium)
	], realtime=True);#, save_replay_as="CarrierSpamBot_vs_VeryHard.SC2Replay");