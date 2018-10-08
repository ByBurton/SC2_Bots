import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls
#from CarrierSpam import CarrierSpamBot

class WarpInArmy(sc2.BotAI):
	#def __init__(self):


	async def on_step(self, iteration):
		if round(self.time) % 3 == 0:
			await self.do_defend();

		if round(self.time) % 6 == 0:
			await self.distribute_workers();  # in sc2/bot_ai.py	
			await self.do_attack();	


		await self.build_pylons();
		await self.expand();
		await self.train_probes();
		await self.build_assimilators();
		await self.build_gate_ways();
		await self.build_cybernetics_core();
		await self.do_cybernetics_research();
		await self.do_warp_in();
		await self.build_forge();
		await self.build_twilight_council();
		await self.do_forge_research();
		await self.do_warp_gates();



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



	async def do_attack(self):
		rays = self.units(VOIDRAY).idle;

		no_attackers = (self.units(STARGATE).amount * 2) + 5;
		if no_attackers > 35:
			no_attackers = 35;

		if rays.exists:
			if rays.amount >= no_attackers:
				for ray in rays:
					await self.do(ray.attack(self.find_target(self.state)));

	#todo: do not follow the enemy back to their base
	async def do_defend(self):
		rays = self.units(VOIDRAY).idle;

		for building in self.units().structure:
			bl_pos = building.position;
			for ray in rays:
				if self.known_enemy_units.closer_than(20, bl_pos).exists:

					#print("defend: idle units: %d; total units: %d" % (forces.amount, nonidle.amount))

					choice = random.choice(self.known_enemy_units.closer_than(20, bl_pos));
					await self.do(ray.attack(choice.position));
				else:
					break;


	async def do_warp_in(self):
		if not self.units(WARPGATE).ready.amount == 25:
			return;

		proxy = self.units(PYLON).closest_to(self.enemy_start_locations[0]);


		total_mineral_cost = (25 * 125) + (25 * 100);
		total_gas_cost = (25 * 50);


		if self.minerals >= total_mineral_cost and self.vespene >= total_gas_cost:
			for gate in self.units(WARPGATE).ready:
				abilities = await self.get_available_abilities(gate);
				# all the units have the same cooldown anyway so let's just look at ZEALOT
				if AbilityId.WARPGATETRAIN_ZEALOT in abilities and self.minerals > 225 and self.vespene > 50:
					pos = proxy.position.to2.random_on_distance(4);
					placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1);
					if placement is None:
						#return ActionResult.CantFindPlacementLocation
						print("Can not warp in unit there!");
						return;

				await self.do(gate.warp_in(STALKER, placement));
				await self.do(gate.warp_in(ZEALOT, placement));

		else:
			return;




	async def expand(self):
		if self.can_afford(UnitTypeId.NEXUS) and not self.already_pending(UnitTypeId.NEXUS):
			#await self.expand_now()
			
			# get_next_expansion returns the center of the mineral fields of the next nearby expansion
			next_expo = await self.get_next_expansion();
			# from the center of mineral fields, we need to find a valid place to place the command center
			location = await self.find_placement(UnitTypeId.NEXUS, next_expo, placement_step=1);
			if location:
				# now we "select" (or choose) the nearest worker to that found location
				w = self.select_build_worker(location);
				if w and self.can_afford(UnitTypeId.NEXUS):
					# the worker will be commanded to build the command center
					error = await self.do(w.build(UnitTypeId.NEXUS, location));
					if error:
						print(error);

	async def build_assimilators(self):
		for nexus in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(10, nexus)
			for vg in vgs:
				if not self.can_afford(ASSIMILATOR) or self.units(PROBE).amount <= 10:
					break;
				worker = self.select_build_worker(vg.position);
				if worker is None:
					break;
				if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
					await self.do(worker.build(ASSIMILATOR, vg));

	async def train_probes(self):
		if self.units(PROBE).amount >= 60:
			return;

		maxprobes = ( self.townhalls.ready.amount * 21 )
		if maxprobes >= 60:
			maxprobes = 60;

		nexi = self.townhalls.ready.noqueue;
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
		nexus = nexi.first;


		if self.units(PYLON).ready.amount < 1:
			if self.supply_left <= supply_no and not self.already_pending(PYLON):
				if self.can_afford(PYLON):
					await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 9));
				return;
		else:
			if self.can_afford(PYLON) and self.units(PYLON).amount < 30:
				await self.build(PYLON, near=self.units(PYLON).ready.random.position.towards(self.game_info.map_center, 3));



	async def build_forge(self):
		if self.townhalls.ready.amount <= 1:
			return;

		if self.units(FORGE).ready.amount < 1 and self.can_afford(FORGE) and not self.already_pending(FORGE):
			await self.build(FORGE, near=self.units(PYLON).closest_to(self.townhalls.ready.first).position);


	async def build_cybernetics_core(self):
		if not self.units(GATEWAY).ready.exists:
			return;

		if self.units(CYBERNETICSCORE).ready.amount < 1 and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
			await self.build(CYBERNETICSCORE, near=self.units(PYLON).closest_to(self.townhalls.ready.first).position);


	async def build_gate_ways(self):
		gates = self.units(WARPGATE) | self.units(GATEWAY);

		if self.townhalls.ready.amount < 3:		
			if gates.ready.amount < 3 and self.can_afford(GATEWAY):
					await self.build(GATEWAY, near=self.units(PYLON).closest_to(self.townhalls.ready.first).position);
		else:
			if gates.ready.amount < 25 and self.can_afford(GATEWAY):
				await self.build(GATEWAY, near=self.units(PYLON).closest_to(self.townhalls.ready.first).position);


	async def build_twilight_council(self):	
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if not self.units(CYBERNETICSCORE).ready.exists:
			return;

		if self.units(TWILIGHTCOUNCIL).ready.amount == 0 and self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
			await self.build(TWILIGHTCOUNCIL, near=self.units(PYLON).closest_to(self.townhalls.ready.first).position);


	async def do_forge_research(self):
		forges = self.units(FORGE).ready.noqueue;
		if not forges.exists:
			return;

		if forges.exists:
			for forge in forges:
				await self.try_upgrade(forge, PROTOSSSHIELDSLEVEL1, FORGERESEARCH_PROTOSSSHIELDSLEVEL1);
				await self.try_upgrade(forge, PROTOSSSHIELDSLEVEL2, FORGERESEARCH_PROTOSSSHIELDSLEVEL2);				
				await self.try_upgrade(forge, PROTOSSSHIELDSLEVEL3, FORGERESEARCH_PROTOSSSHIELDSLEVEL3);
				await self.try_upgrade(forge, PROTOSSGROUNDWEAPONSLEVEL1, FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1);
				await self.try_upgrade(forge, PROTOSSGROUNDWEAPONSLEVEL2, FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2);
				await self.try_upgrade(forge, PROTOSSGROUNDWEAPONSLEVEL3, FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3);
				await self.try_upgrade(forge, PROTOSSGROUNDARMORSLEVEL1, FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1);
				await self.try_upgrade(forge, PROTOSSGROUNDARMORSLEVEL2, FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2);
				await self.try_upgrade(forge, PROTOSSGROUNDARMORSLEVEL3, FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3);

	async def do_cybernetics_research(self):
		cores = self.units(CYBERNETICSCORE).ready.noqueue;
		if cores.exists:
			for core in cores:
				await self.try_upgrade(core, WARPGATERESEARCH, RESEARCH_WARPGATE);
				await self.try_upgrade(core, CHARGE, RESEARCH_CHARGE);
				#await self.try_upgrade(core, , RESEARCH_ADEPTRESONATINGGLAIVES);


	async def do_warp_gates(self):
		if not WARPGATERESEARCH in self.state.upgrades:
			return;

		for gateway in self.units(GATEWAY).ready:
			abilities = await self.get_available_abilities(gateway);
			if AbilityId.MORPH_WARPGATE in abilities and self.can_afford(AbilityId.MORPH_WARPGATE):
				await self.do(gateway(MORPH_WARPGATE));


#runs the actual game
run_game(maps.get("AbyssalReefLE"), [
	#Human(Race.Terran),
	Bot(Race.Protoss, WarpInArmy()),
	Computer(Race.Random, Difficulty.VeryEasy)
	], realtime=False);

#Computer.Difficulty:
	#VeryEasy,
    #Easy,
    #Medium,
    #MediumHard,
    #Hard,
    #Harder,
    #VeryHard,
    #CheatVision,
    #CheatMoney,
    #CheatInsane