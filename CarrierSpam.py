import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls

class CarrierSpamBot(sc2.BotAI):
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
		await self.build_gate_way();
		await self.build_cybernetics_core();
		await self.build_fleet_beacon();
		await self.do_fleet_beacon_research();
		await self.do_cybernetics_research();
		await self.build_forge();
		await self.build_twilight_council();
		await self.do_forge_research();
		await self.build_stargates();
		await self.train_carriers();
		await self.build_static_defenses();



	async def do_attack(self):
		carriers = self.units(CARRIER).idle;

		no_attackers = (self.units(STARGATE).amount * 1) + 5; #attack with at least 6 carriers
		if no_attackers > 18:
			no_attackers = 18;

		if carriers.exists:
			if carriers.amount >= no_attackers:
				for carrier in carriers:
					await self.do(carrier.attack(self.find_target(self.state)));


	#todo: do not follow the enemy back to their base
	async def do_defend(self):
		carriers = self.units(CARRIER).idle;

		for building in self.units().structure:
			bl_pos = building.position;
			for carrier in carriers:
				if self.known_enemy_units.closer_than(20, bl_pos).exists:

					#print("defend: idle units: %d; total units: %d" % (forces.amount, nonidle.amount))

					choice = random.choice(self.known_enemy_units.closer_than(20, bl_pos));
					await self.do(carrier.attack(choice.position));
				else:
					break;


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
			vgs = self.state.vespene_geyser.closer_than(8, nexus);
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
		nexus = nexi.random;

		supply_no = 6 * self.units(STARGATE).ready.amount;
		if supply_no == 0:
			supply_no = 6;

		if self.units(PYLON).ready.amount >= 40:
			return;

		if self.supply_left <= supply_no and not self.already_pending(PYLON):
			if self.can_afford(PYLON):
				await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 10));
			return;


	async def build_stargates(self):
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if not self.units(CYBERNETICSCORE).ready.exists:
			return;

		if not self.units(FLEETBEACON).exists and self.units(STARGATE).ready.amount >= 1:
			return;


		if self.units(STARGATE).amount < self.townhalls.ready.amount and (self.minerals >= 800 and self.vespene >= 800):
			if self.units(STARGATE).amount >= 1:
				if not PROTOSSSHIELDSLEVEL3 in self.state.upgrades and not self.already_pending(PROTOSSSHIELDSLEVEL3):
					return;
				if not PROTOSSAIRWEAPONSLEVEL3 in self.state.upgrades and not self.already_pending(PROTOSSAIRWEAPONSLEVEL3):
					return;
				if not PROTOSSAIRARMORSLEVEL3 in self.state.upgrades and not self.already_pending(PROTOSSAIRARMORSLEVEL3):
					return;
						
			if self.can_afford(STARGATE):
				await self.build(STARGATE, near=pylon);


	async def build_forge(self):
		if self.townhalls.ready.amount <= 1:
			return;

		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if self.units(FORGE).ready.amount < 1 and self.can_afford(FORGE) and not self.already_pending(FORGE):
			await self.build(FORGE, near=pylon);


	async def build_cybernetics_core(self):
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if not self.units(GATEWAY).ready.exists:
			return;

		if self.units(CYBERNETICSCORE).ready.amount < 2 and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
			await self.build(CYBERNETICSCORE, near=pylon);


	async def build_gate_way(self):
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if self.units(GATEWAY).ready.amount < 1 and self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
			await self.build(GATEWAY, near=pylon);


	async def build_fleet_beacon(self):
		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if self.units(STARGATE).ready.amount == 0:
			return;

		if self.units(FLEETBEACON).ready.amount == 0 and self.can_afford(FLEETBEACON) and not self.already_pending(FLEETBEACON):
			await self.build(FLEETBEACON, near=pylon);


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


	async def train_carriers(self):
		if not self.units(FLEETBEACON).ready.exists:
			return;

		#prio to upgrades
		if not PROTOSSSHIELDSLEVEL3 in self.state.upgrades:
			if self.units(FORGE).ready.noqueue.exists:
				return;
		elif not PROTOSSAIRWEAPONSLEVEL3 in self.state.upgrades:
			if self.units(CYBERNETICSCORE).ready.noqueue.exists:
				return;
		elif not PROTOSSAIRARMORSLEVEL3 in self.state.upgrades:
			if self.units(CYBERNETICSCORE).ready.noqueue.exists:
				return;

		for sg in self.units(STARGATE).ready.noqueue:
			if self.can_afford(CARRIER) and self.supply_left >= 6:
				await self.do(sg.train(CARRIER));


	async def do_forge_research(self):
		forges = self.units(FORGE).ready.noqueue;
		if not forges.exists:
			return;

		if forges.exists:
			for forge in forges:
				if self.can_afford(PROTOSSSHIELDSLEVEL1) and not PROTOSSSHIELDSLEVEL1 in self.state.upgrades and not self.already_pending(PROTOSSSHIELDSLEVEL1):
					await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1));				
				elif self.can_afford(PROTOSSSHIELDSLEVEL2) and not PROTOSSSHIELDSLEVEL2 in self.state.upgrades and not self.already_pending(PROTOSSSHIELDSLEVEL2) and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2));	
				elif self.can_afford(PROTOSSSHIELDSLEVEL3) and not PROTOSSSHIELDSLEVEL3 in self.state.upgrades and not self.already_pending(PROTOSSSHIELDSLEVEL3) and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3));	


	async def do_cybernetics_research(self):
		cores = self.units(CYBERNETICSCORE).ready.noqueue;
		if cores.exists:
			for core in cores:
				if self.can_afford(PROTOSSAIRWEAPONSLEVEL1) and not PROTOSSAIRWEAPONSLEVEL1 in self.state.upgrades and not self.already_pending(PROTOSSAIRWEAPONSLEVEL1):
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1));
				elif self.can_afford(PROTOSSAIRWEAPONSLEVEL2) and not PROTOSSAIRWEAPONSLEVEL2 in self.state.upgrades and not self.already_pending(PROTOSSAIRWEAPONSLEVEL2) and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2));
				elif self.can_afford(PROTOSSAIRWEAPONSLEVEL3) and not PROTOSSAIRWEAPONSLEVEL3 in self.state.upgrades and not self.already_pending(PROTOSSAIRWEAPONSLEVEL3) and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3));
				elif self.can_afford(PROTOSSAIRARMORSLEVEL1) and not PROTOSSAIRARMORSLEVEL1 in self.state.upgrades and not self.already_pending(PROTOSSAIRARMORSLEVEL1):
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1));	
				elif self.can_afford(PROTOSSAIRARMORSLEVEL2) and not PROTOSSAIRARMORSLEVEL2 in self.state.upgrades and not self.already_pending(PROTOSSAIRARMORSLEVEL2) and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2));
				elif self.can_afford(PROTOSSAIRARMORSLEVEL3) and not PROTOSSAIRARMORSLEVEL3 in self.state.upgrades and not self.already_pending(PROTOSSAIRARMORSLEVEL3) and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3));


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


	async def do_fleet_beacon_research(self):
		beacons = self.units(FLEETBEACON).ready.noqueue;
		if beacons.exists:
			for beacon in beacons:
				await self.try_upgrade(beacon, CARRIERLAUNCHSPEEDUPGRADE, AbilityId.RESEARCH_INTERCEPTORGRAVITONCATAPULT);
#FLEETBEACONRESEARCH_RESEARCHINTERCEPTORLAUNCHSPEEDUPGRADE


	async def build_static_defenses(self):
		if self.minerals < 1300 or not self.units(FLEETBEACON).ready.exists:
			return;

		pylons = self.units(PYLON).ready;
		if pylons.exists:
			pylon = pylons.random;
		else:
			return;

		if not self.units(FORGE).ready.exists:
			return;

		#build a cannon and battery
		if self.can_afford(PHOTONCANNON):
			await self.build(PHOTONCANNON, near=pylon.position.towards(self.game_info.map_center, 4));
			if self.can_afford(SHIELDBATTERY) and self.units(SHIELDBATTERY).amount <= self.units(PHOTONCANNON).amount / 3:
				await self.build(SHIELDBATTERY, near=pylon.position.towards(self.game_info.map_center, -2));




#runs the actual game
#run_game(maps.get("AbyssalReefLE"), [
run_game(maps.get("AbyssalReefLE"), [
	Human(Race.Zerg),
	Bot(Race.Protoss, CarrierSpamBot())#,
	#Computer(Race.Protoss, Difficulty.VeryHard)
	], realtime=True);#, save_replay_as="CarrierSpamBot_vs_VeryHard.SC2Replay");