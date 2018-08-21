import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls

class BattleCruiserRushBot(sc2.BotAI):
	#def __init__(self):



	async def on_step(self, iteration):
		if round(self.time) % 10 == 0:
			await self.distribute_workers()  # in sc2/bot_ai.py	
			await self.do_attack()
		if round(self.time) % 5 == 0:
			await self.do_defend()


		await self.train_scvs()
		await self.build_refineries()
		await self.build_supply_depots()
		await self.expand()
		await self.build_barracks()
		await self.build_factory()
		await self.build_armories()
		await self.build_starports()
		await self.build_starport_addons()
		await self.build_fusion_core()
		await self.do_research()
		await self.train_battle_cruisers()
		await self.do_repairs()


	def find_target(self, state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units).position
		elif len(self.known_enemy_structures):
			return random.choice(self.known_enemy_structures).position
		else:
			return self.enemy_start_locations[0]


	async def do_attack(self):
		bcs = self.units(BATTLECRUISER).idle

		no_attackers = 20

		if bcs.exists:
			if bcs.amount >= no_attackers:
				for cruiser in bcs:
					await self.do(cruiser.attack(self.find_target(self.state)))

	#todo: do not follow the enemy back to their base
	async def do_defend(self):
		bcs = self.units(BATTLECRUISER).idle

		for building in self.units().structure:
			bl_pos = building.position
			for cruiser in bcs:
				if self.known_enemy_units.closer_than(20, bl_pos).exists:

					#print("defend: idle units: %d; total units: %d" % (forces.amount, nonidle.amount))

					choice = random.choice(self.known_enemy_units.closer_than(20, bl_pos))
					await self.do(cruiser.attack(choice.position))
				else:
					break


	async def expand(self):
		if self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(UnitTypeId.COMMANDCENTER):
			#await self.expand_now()
			
			# get_next_expansion returns the center of the mineral fields of the next nearby expansion
			next_expo = await self.get_next_expansion()
			# from the center of mineral fields, we need to find a valid place to place the command center
			location = await self.find_placement(UnitTypeId.COMMANDCENTER, next_expo, placement_step=1)
			if location:
				# now we "select" (or choose) the nearest worker to that found location
				w = self.select_build_worker(location)
				if w and self.can_afford(UnitTypeId.COMMANDCENTER):
					# the worker will be commanded to build the command center
					error = await self.do(w.build(UnitTypeId.COMMANDCENTER, location))
					if error:
						print(error)

	async def build_refineries(self):
		for cc in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(10, cc)
			for vg in vgs:
				if not self.can_afford(REFINERY) or self.units(SCV).amount <= 10:
					break
				worker = self.select_build_worker(vg.position)
				if worker is None:
					break
				if not self.units(REFINERY).closer_than(1.0, vg).exists:
					await self.do(worker.build(REFINERY, vg))

	async def train_scvs(self):
		if self.units(SCV).amount >= 68:
			return

		maxscvs = ( self.townhalls.ready.amount * 22 )
		if maxscvs >= 68:
			maxscvs = 68

		commandcenters = self.townhalls.ready.noqueue
		if commandcenters.exists:
			for cc in commandcenters:
				if self.can_afford(SCV) and self.supply_left >= 1 and self.units(SCV).amount < maxscvs:
					await self.do(cc.train(SCV))

	async def build_supply_depots(self):
		cc = self.townhalls.random

		if self.supply_left <= 6 and self.can_afford(SUPPLYDEPOT):
			await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, -15))

	async def build_barracks(self):
		#pos =self.game_info.map_center.towards(self.enemy_start_locations[0], 10)

		cc = self.townhalls.ready.first

		if self.units(BARRACKS).amount < 1 and self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
			await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 10))

	async def build_factory(self):
		cc = self.townhalls.ready.first

		if self.units(BARRACKS).ready.exists and self.units(FACTORY).amount < 1 and self.can_afford(FACTORY) and not self.already_pending(FACTORY):
			await self.build(FACTORY, near=cc.position.towards(self.game_info.map_center, 10))

	async def build_armories(self):
		cc = self.townhalls.ready.first
		
		if self.units(FACTORY).ready.exists and self.units(ARMORY).amount < 2 and self.can_afford(ARMORY) and not self.already_pending(ARMORY):
			await self.build(ARMORY, near=cc.position.towards(self.game_info.map_center, 7))

	async def build_starports(self):
		cc = self.townhalls.ready.first
		
		if self.units(STARPORT).amount < self.townhalls.ready.amount + 1 or (self.minerals >= 800 and self.vespene >= 800):
			if self.units(STARPORT).amount >= 1:
				if not TERRANVEHICLEARMORSLEVEL3 in self.state.upgrades and not self.already_pending(TERRANVEHICLEARMORSLEVEL3):
					return
				if not TERRANSHIPWEAPONSLEVEL3 in self.state.upgrades and not self.already_pending(TERRANSHIPWEAPONSLEVEL3):
					return
				if self.units(FUSIONCORE).amount < 1 and not self.units(STARPORT).amount < 1:
					return

		if self.units(FACTORY).ready.exists and self.units(STARPORT).amount < self.townhalls.ready.amount and self.can_afford(STARPORT) and not self.already_pending(STARPORT):
			await self.build(STARPORT, near=cc.position.towards(self.game_info.map_center, -5))

	async def build_fusion_core(self):
		cc = self.townhalls.ready.first

		if self.units(STARPORT).amount < 1:
			return

		if self.units(FUSIONCORE).amount >= 1 or not self.can_afford(FUSIONCORE):
			return

		await self.build(FUSIONCORE, near=cc.position.towards(self.game_info.map_center, 5))

	async def train_battle_cruisers(self):
		#if not TERRANSHIPWEAPONSLEVEL3 in self.state.upgrades:
				#return
		#elif not TERRANVEHICLEARMORSLEVEL3 in self.state.upgrades:
				#return

		for sg in self.units(STARPORT).ready.noqueue:
			if self.can_afford(BATTLECRUISER) and self.supply_left >= 6:
				await self.do(sg.train(BATTLECRUISER))

	async def try_upgrade(self, facility, upgrade_id, ability_id):
		#not self.already_pending(upgrade_id) 
		if self.can_afford(upgrade_id) and not upgrade_id in self.state.upgrades:
			if self.has_ability(ability_id, facility):
				await self.do(facility(ability_id))

	# Check if a unit has an ability available (also checks upgrade costs??)
	async def has_ability(self, ability, unit):
		abilities = await self.get_available_abilities(unit)
		if ability in abilities:
			return True
		else:
			return False


	async def do_research(self):
		for facility in self.units(ARMORY).ready.noqueue:
			await self.try_upgrade(facility, TERRANVEHICLEANDSHIPARMORSLEVEL1, AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL1)
			await self.try_upgrade(facility, TERRANVEHICLEANDSHIPARMORSLEVEL2, AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL2)
			await self.try_upgrade(facility, TERRANVEHICLEANDSHIPARMORSLEVEL3, AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL3)
			await self.try_upgrade(facility, TERRANSHIPWEAPONSLEVEL1, AbilityId.ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL1)
			await self.try_upgrade(facility, TERRANSHIPWEAPONSLEVEL2, AbilityId.ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL2)
			await self.try_upgrade(facility, TERRANSHIPWEAPONSLEVEL3, AbilityId.ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL3)

	async def build_starport_addons(self):
		for port in self.units(STARPORT).ready.noqueue:
			if self.can_afford(STARPORTTECHLAB) and not port.add_on_tag == 0:
				await self.do(port.build(STARPORTTECHLAB))				

	async def do_repairs(self):
		scv = self.units(SCV).random

		for bc in self.units(BATTLECRUISER):
			if bc.health < bc.health_max:
				await self.do(scv(AbilityId.EFFECT_REPAIR_SCV, bc))


#runs the actual game
#run_game(maps.get("AbyssalReefLE"), [
run_game(maps.get("BelShirVestigeLE"), [
	#Human(Race.Zerg),
	Bot(Race.Terran, BattleCruiserRushBot()),
	Computer(Race.Zerg, Difficulty.VeryEasy)
	], realtime=False)