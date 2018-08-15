import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls

class VoidRaySpamBot(sc2.BotAI):
	def __init__(self):
		self.weapons_1 = False
		self.weapons_2 = False
		self.weapons_3 = False
		self.shields_1 = False
		self.shields_2 = False
		self.shields_3 = False
		self.armor_1 = False
		self.armor_2 = False
		self.armor_3 = False
		self.charge = False

	async def on_step(self, iteration):
		if round(self.time) % 3 == 0:
			await self.do_defend()

		if round(self.time) % 6 == 0:
			await self.distribute_workers()  # in sc2/bot_ai.py	
			await self.do_attack()		

		await self.build_pylons()
		await self.expand()
		await self.train_probes()
		await self.build_assimilators()
		await self.build_gate_way()
		await self.build_cybernetics_core()
		await self.build_fleet_beacon()
		await self.do_cybernetics_research()
		await self.build_forge()
		await self.build_twilight_council()
		await self.do_forge_research()
		await self.build_stargates()
		await self.train_void_rays()



	async def do_attack(self):
		rays = self.units(VOIDRAY).idle

		no_attackers = (self.units(STARGATE).amount * 2) + 5
		if no_attackers >= 35:
			no_attackers = 35

		if rays.exists:
			if rays.amount >= no_attackers:
				for ray in rays:
					await self.do(ray.attack(self.find_target(self.state)))

	#todo: do not follow the enemy back to their base
	async def do_defend(self):
		rays = self.units(VOIDRAY).idle

		for building in self.units().structure:
			bl_pos = building.position
			for ray in rays:
				if self.known_enemy_units.closer_than(20, bl_pos).exists:

					#print("defend: idle units: %d; total units: %d" % (forces.amount, nonidle.amount))

					choice = random.choice(self.known_enemy_units.closer_than(20, bl_pos))
					await self.do(ray.attack(choice.position))
				else:
					break

	async def expand(self):
		if self.can_afford(UnitTypeId.NEXUS) and not self.already_pending(UnitTypeId.NEXUS):
			#await self.expand_now()
			
			# get_next_expansion returns the center of the mineral fields of the next nearby expansion
			next_expo = await self.get_next_expansion()
			# from the center of mineral fields, we need to find a valid place to place the command center
			location = await self.find_placement(UnitTypeId.NEXUS, next_expo, placement_step=1)
			if location:
				# now we "select" (or choose) the nearest worker to that found location
				w = self.select_build_worker(location)
				if w and self.can_afford(UnitTypeId.NEXUS):
					# the worker will be commanded to build the command center
					error = await self.do(w.build(UnitTypeId.NEXUS, location))
					if error:
						print(error)

	async def build_assimilators(self):
		for nexus in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(10, nexus)
			for vg in vgs:
				if not self.can_afford(ASSIMILATOR) or self.units(PROBE).amount <= 10:
					break
				worker = self.select_build_worker(vg.position)
				if worker is None:
					break
				if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
					await self.do(worker.build(ASSIMILATOR, vg))

	async def train_probes(self):
		if self.units(PROBE).amount >= 50:
			return

		maxprobes = ( self.townhalls.ready.amount * 21 )
		if maxprobes >= 60:
			maxprobes = 60

		nexi = self.townhalls.ready.noqueue
		if nexi.exists:
			for nexus in nexi:
				if self.can_afford(PROBE) and self.supply_left >= 1 and self.units(PROBE).amount <= maxprobes:
					await self.do(nexus.train(PROBE))


	def find_target(self, state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units).position
		elif len(self.known_enemy_structures):
			return random.choice(self.known_enemy_structures).position
		else:
			return self.enemy_start_locations[0]

	async def build_pylons(self):
		nexi = self.townhalls.ready
		if not nexi.exists:
			return
		nexus = nexi.first

		supply_no = 4 * self.units(STARGATE).ready.amount
		if supply_no == 0:
			supply_no = 2

		if self.supply_left <= supply_no and not self.already_pending(PYLON):
			if self.can_afford(PYLON):
				await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 5))
			return

	async def build_stargates(self):
		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if not self.units(CYBERNETICSCORE).ready.exists:
			return

		if not self.units(FLEETBEACON).exists and self.units(STARGATE).ready.amount >= 1:
			return


		if self.units(STARGATE).amount < self.townhalls.ready.amount + 1 or self.minerals >= 700 and self.vespene >= 800:
			if self.weapons_3 == False:
				if self.units(CYBERNETICSCORE).ready.noqueue.exists:
					return
			if self.armor_3 == False:
				if self.units(CYBERNETICSCORE).ready.noqueue.exists:
					return
			if self.shields_3 == False:
				if self.units(FORGE).ready.noqueue.exists:
					return
			if self.can_afford(STARGATE):
				await self.build(STARGATE, near=pylon)


	async def build_forge(self):
		if self.townhalls.ready.amount <= 1:
			return

		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if self.units(FORGE).ready.amount < 1 and self.can_afford(FORGE) and not self.already_pending(FORGE):
			await self.build(FORGE, near=pylon)

	async def build_cybernetics_core(self):
		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if not self.units(GATEWAY).ready.exists:
			return

		if self.units(CYBERNETICSCORE).ready.amount < 2 and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
			await self.build(CYBERNETICSCORE, near=pylon)

	async def build_gate_way(self):
		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if self.units(GATEWAY).ready.amount < 1 and self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
			await self.build(GATEWAY, near=pylon)

	async def build_fleet_beacon(self):
		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if self.units(STARGATE).ready.amount == 0:
			return

		if self.units(FLEETBEACON).ready.amount == 0 and self.can_afford(FLEETBEACON) and not self.already_pending(FLEETBEACON):
			await self.build(FLEETBEACON, near=pylon)

	async def build_twilight_council(self):	
		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if not self.units(CYBERNETICSCORE).ready.exists:
			return

		if self.units(TWILIGHTCOUNCIL).ready.amount == 0 and self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
			await self.build(TWILIGHTCOUNCIL, near=pylon)

	async def train_void_rays(self):
		if self.weapons_3 == False:
			if self.units(CYBERNETICSCORE).ready.noqueue.exists:
				return
		if self.armor_3 == False:
			if self.units(CYBERNETICSCORE).ready.noqueue.exists:
				return
		if self.shields_3 == False:
			if self.units(FORGE).ready.noqueue.exists:
				return

		for sg in self.units(STARGATE).ready.noqueue:
			if self.can_afford(VOIDRAY) and self.supply_left >= 4:
				await self.do(sg.train(VOIDRAY))

	async def do_forge_research(self):
		forges = self.units(FORGE).ready.noqueue
		if not forges.exists:
			return

		if forges.exists:
			for forge in forges:
				if self.can_afford(PROTOSSSHIELDSLEVEL1) and self.shields_1 == False:
					#await self.do(forge.research(PROTOSSSHIELDSLEVEL1))
					await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1))					
					self.shields_1 = True
				elif self.can_afford(PROTOSSSHIELDSLEVEL2) and self.shields_2 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					#await self.do(forge.research(PROTOSSSHIELDSLEVEL2))
					await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2))		
					self.shields_2 = True
				elif self.can_afford(PROTOSSSHIELDSLEVEL3) and self.shields_3 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					#await self.do(forge.research(PROTOSSSHIELDSLEVEL3))
					await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3))		
					self.shields_3 = True

	async def do_cybernetics_research(self):
		cores = self.units(CYBERNETICSCORE).ready.noqueue
		if cores.exists:
			for core in cores:
				if self.can_afford(PROTOSSAIRWEAPONSLEVEL1) and self.weapons_1 == False:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1))
					self.weapons_1 = True
				elif self.can_afford(PROTOSSAIRWEAPONSLEVEL2) and self.weapons_2 == False and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2))
					self.weapons_2 = True
				elif self.can_afford(PROTOSSAIRWEAPONSLEVEL3) and self.weapons_3 == False and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3))
					self.weapons_3 = True
				elif self.can_afford(PROTOSSAIRARMORSLEVEL1) and self.armor_1 == False:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL1))	
					self.armor_1 = True
				elif self.can_afford(PROTOSSAIRARMORSLEVEL2) and self.armor_2 == False and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL2))
					self.armor_2 = True
				elif self.can_afford(PROTOSSAIRARMORSLEVEL3) and self.armor_3 == False and self.units(FLEETBEACON).ready.amount >= 1:
					await self.do(core(AbilityId.CYBERNETICSCORERESEARCH_PROTOSSAIRARMORLEVEL3))
					self.armor_3 = True	



#runs the actual game
run_game(maps.get("AbyssalReefLE"), [
	#Human(Race.Terran),
	Bot(Race.Protoss, VoidRaySpamBot()),
	Computer(Race.Zerg, Difficulty.VeryHard)
	], realtime=False)