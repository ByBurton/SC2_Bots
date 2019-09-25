import sc2;
import random;

from sc2 import run_game, maps, Race, Difficulty;
from sc2.player import Bot, Computer, Human;
from sc2.constants import *;
from sc2.data import race_townhalls;

class CreeperBot(sc2.BotAI):

	async def on_step(self, iteration):
		await self.distribute_workers();
		await self.expand();
		await self.upgrade_townhalls();

		await self.train_drones();
		await self.train_overlords();
		await self.train_queens();

		await self.build_spawning_pool();
		await self.build_infestation_pit();
		await self.build_extractors();

		await self.spawn_larvae();

		await self.move_overlords();




	def is_enemy_near(self):
		for building in self.units().structure:
			bl_pos = building.position;
			if self.known_enemy_units.closer_than(20, bl_pos).exists:
				return True;
			else:
				return False;

	def find_target(self, state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units).position;
		elif len(self.known_enemy_structures):
			return random.choice(self.known_enemy_structures).position;
		else:
			return self.enemy_start_locations[0];


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


	async def build_extractors(self):
		for hatchery in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(10, hatchery)
			for vg in vgs:
				if not self.can_afford(EXTRACTOR) or self.units(DRONE).amount <= 13:
					break;
				worker = self.select_build_worker(vg.position);
				if worker is None:
					break;
				if not self.units(EXTRACTOR).closer_than(1.0, vg).exists:
					await self.do(worker.build(EXTRACTOR, vg));

	async def train_drones(self):
		maxDrones = self.townhalls.amount * 21;
		if maxDrones >  65:
			maxDrones = 65;

		for larva in self.units(LARVA):
			if self.is_enemy_near() == True and self.units(DRONE).amount >= self.townhalls.amount * 5 and self.can_afford(HYDRALISK) and self.units(HYDRALISKDEN).ready.exists:
				return;
			elif self.can_afford(DRONE) and self.supply_left >= 1 and self.units(DRONE).amount < maxDrones:
				await self.do(larva.train(DRONE));

	async def train_overlords(self):
		for larva in self.units(LARVA):
			if self.supply_left <= 8 * self.townhalls.ready.amount and self.units(OVERLORD).amount <= 25 and self.can_afford(OVERLORD) and not self.already_pending(OVERLORD):
				await self.do(larva.train(OVERLORD));

	async def train_queens(self):
		if self.can_afford(QUEEN) and self.units(SPAWNINGPOOL).ready.exists and self.units(QUEEN).amount < self.townhalls.amount + 2 and self.supply_left >= 2:
			hatcheries = self.townhalls.ready.noqueue;
			if hatcheries.exists:
				for hatchery in hatcheries:
					if self.can_afford(QUEEN) and not self.already_pending(QUEEN):
						await self.do(hatchery.train(QUEEN));

	async def expand(self):
		if self.can_afford(UnitTypeId.HATCHERY) and not self.already_pending(UnitTypeId.HATCHERY):
			await self.expand_now();

	async def build_spawning_pool(self):
		townhall = self.townhalls.ready.first;

		if self.can_afford(SPAWNINGPOOL) and not self.already_pending(SPAWNINGPOOL) and self.units(SPAWNINGPOOL).amount < 1:
			await self.build(SPAWNINGPOOL, near=townhall.position.towards(self.game_info.map_center, 8));


	async def build_infestation_pit(self):
		townhall = self.townhalls.ready.first;

		if self.can_afford(INFESTATIONPIT) and not self.already_pending(INFESTATIONPIT) and self.units(INFESTATIONPIT).amount < 1 and (self.units(LAIR).ready.exists or self.units(HIVE).ready.exists):
			await self.build(INFESTATIONPIT, near=townhall.position.towards(self.game_info.map_center, 6));

	async def spawn_larvae(self):
		for hatch in self.townhalls.ready:
			if not hatch.has_buff(QUEENSPAWNLARVATIMER) and self.units(QUEEN).exists:
				lucky = self.units(QUEEN).closest_to(hatch);
				abilities = await self.get_available_abilities(lucky);
				if AbilityId.EFFECT_INJECTLARVA in abilities and lucky.energy > 25:
					await self.do(lucky(EFFECT_INJECTLARVA, hatch));

	#move overlords around. "I see you! You can not hide."
	async def move_overlords(self):
		for overlord in self.units(OVERLORD).idle:
			hatcheries = self.townhalls.ready;
			if hatcheries.exists:
				hatchery = hatcheries.random;
				pos = hatchery.position.random_on_distance(20);
				await self.do(overlord.move(pos));


	async def upgrade_townhalls(self):
		if self.units(QUEEN).amount < self.townhalls.ready.amount:
			return;

		for tier1 in self.units(HATCHERY).ready.noqueue:
			if self.can_afford(LAIR) and self.units(SPAWNINGPOOL).ready.exists:
				if self.already_pending(LAIR) or self.already_pending(HIVE) or self.units(LAIR).ready.exists or self.units(HIVE).ready.exists:
					break;
				else:
					await self.do(tier1.build(LAIR));
		for tier2 in self.units(LAIR).ready.noqueue:
			if self.can_afford(HIVE) and self.units(INFESTATIONPIT).ready.exists:
				if self.already_pending(HIVE) or self.units(HIVE).ready.exists:
					break;
				else:
					await self.do(tier2.build(HIVE));


	async def do_attack(self):
		mutas = self.units(MUTALISK).idle;

		no_attackers = 40

		if mutas.exists:
			if mutas.amount >= no_attackers:
				for muta in mutas:
					await self.do(muta.attack(self.find_target(self.state)));


	#todo: do not follow the enemy back to their base
	async def do_defend(self):
		mutas = self.units(MUTALISK).idle;

		for building in self.units().structure:
			bl_pos = building.position;
			for muta in mutas:
				if self.known_enemy_units.closer_than(17, bl_pos).exists:

					#print("defend: idle units: %d; total units: %d" % (forces.amount, nonidle.amount))

					choice = random.choice(self.known_enemy_units.closer_than(17, bl_pos));
					await self.do(muta.attack(choice.position));
				else:
					break;



#runs the actual game
run_game(maps.get("StasisLE"), [
	#Human(Race.Protoss),
	Bot(Race.Zerg, CreeperBot()),
	Computer(Race.Random, Difficulty.VeryEasy)
	], realtime=True, save_replay_as="CreeperBot_vs_VeryEasy.SC2Replay");