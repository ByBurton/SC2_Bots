import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls
#from terran import BotName

class ZealotRushBot(sc2.BotAI):
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
		await self.distribute_workers()  # in sc2/bot_ai.py
		await self.build_pylons()
		await self.expand()
		await self.train_probes()
		await self.build_assimilators()
		await self.build_gateways()
		await self.build_forges()
		await self.build_cybernetics_core()
		await self.build_twilight_council()
		await self.do_forge_research()
		await self.do_tc_research()
		await self.train_zealots()
		await self.do_attack()
		await self.do_defend()


	async def do_attack(self):
		zealots = self.units(ZEALOT).idle

		no_attackers = (self.units(GATEWAY).amount * 5) + 2
		if no_attackers >= 75:
			no_attackers = 75

		if zealots.exists:
			if zealots.amount >= no_attackers:
				for zealot in zealots:
					await self.do(zealot.attack(self.find_target(self.state)))

	#todo: do not follow the enemy back to their base
	async def do_defend(self):
		zealots = self.units(ZEALOT).idle

		for building in self.units().structure:
			bl_pos = building.position
			for zealot in zealots:
				if self.known_enemy_units.closer_than(25, bl_pos).exists:

					#print("defend: idle units: %d; total units: %d" % (forces.amount, nonidle.amount))

					choice = random.choice(self.known_enemy_units.closer_than(26, bl_pos))
					await self.do(zealot.attack(choice.position))
				else:
					break

	async def expand(self):
		if self.can_afford(NEXUS) and not self.already_pending(NEXUS):
			await self.expand_now()

	async def build_assimilators(self):
		for nexus in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(10, nexus)
			for vg in vgs:
				if not self.can_afford(ASSIMILATOR) or self.units(PROBE).amount <= 16:
					break
				worker = self.select_build_worker(vg.position)
				if worker is None:
					break
				if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
					await self.do(worker.build(ASSIMILATOR, vg))

	async def train_probes(self):
		if self.units(PROBE).amount >= 50:
			return

		maxprobes = ( self.townhalls.ready.amount * 17 ) + 1
		if maxprobes >= 50 :
			maxprobes = 50

		nexi = self.townhalls.ready.noqueue
		if nexi.exists:
			for nexus in nexi:
				if self.can_afford(PROBE) and self.supply_left >= 1:
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

		supply_no = 2 * self.units(GATEWAY).ready.amount
		if supply_no == 0:
			supply_no = 2

		if self.supply_left <= supply_no and not self.already_pending(PYLON):
			if self.can_afford(PYLON):
				await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 5))
			return

	async def build_gateways(self):
		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return


		if self.units(GATEWAY).amount == 0 or self.minerals > 500:
			if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
				await self.build(GATEWAY, near=pylon)


	async def build_forges(self):
		if self.units(PROBE).amount <= 30 and self.townhalls.ready.amount < 2:
			return

		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if self.units(FORGE).ready.amount < 2 and self.can_afford(FORGE) and not self.already_pending(FORGE):
			await self.build(FORGE, near=pylon)

	async def build_cybernetics_core(self):
		if self.units(PROBE).amount <= 30 and self.townhalls.ready.amount < 2:
			return

		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if self.units(CYBERNETICSCORE).ready.amount == 0 and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
			await self.build(CYBERNETICSCORE, near=pylon)

	async def build_twilight_council(self):
		if self.units(PROBE).amount <= 30 and self.townhalls.ready.amount < 2:
			return
	
		pylons = self.units(PYLON).ready
		if pylons.exists:
			pylon = pylons.random
		else:
			return

		if self.units(TWILIGHTCOUNCIL).ready.amount == 0 and self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
			await self.build(TWILIGHTCOUNCIL, near=pylon)

	async def train_zealots(self):
		for gw in self.units(GATEWAY).ready.noqueue:
			if self.can_afford(ZEALOT) and self.supply_left >= 2:
				await self.do(gw.train(ZEALOT))

	async def do_forge_research(self):
		forges = self.units(FORGE).ready.noqueue
		if not forges.exists:
			return

		if forges.exists:
			for forge in forges:
				if self.can_afford(PROTOSSGROUNDWEAPONSLEVEL1) and self.weapons_1 == False:
					await self.do(forge.research(PROTOSSGROUNDWEAPONSLEVEL1))
					self.weapons_1 = True
				if self.can_afford(PROTOSSGROUNDWEAPONSLEVEL2) and self.weapons_2 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge.research(PROTOSSGROUNDWEAPONSLEVEL2))
					self.weapons_2 = True
				if self.can_afford(PROTOSSGROUNDWEAPONSLEVEL3) and self.weapons_3 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge.research(PROTOSSGROUNDWEAPONSLEVEL3))
					self.weapons_3 = True
				if self.can_afford(PROTOSSSHIELDSLEVEL1) and self.shields_1 == False:
					await self.do(forge.research(PROTOSSSHIELDSLEVEL1))
					self.shields_1 = True
				if self.can_afford(PROTOSSSHIELDSLEVEL2) and self.shields_2 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge.research(PROTOSSSHIELDSLEVEL2))
					self.shields_2 = True
				if self.can_afford(PROTOSSSHIELDSLEVEL3) and self.shields_3 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge.research(PROTOSSSHIELDSLEVEL3))
					self.shields_3 = True
				if self.can_afford(PROTOSSGROUNDARMORSLEVEL1) and self.armor_1 == False:
					await self.do(forge.research(PROTOSSGROUNDARMORSLEVEL1))
					self.armor_1 = True
				if self.can_afford(PROTOSSGROUNDARMORSLEVEL2) and self.armor_2 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge.research(PROTOSSGROUNDARMORSLEVEL2))
					self.armor_2 = True
				if self.can_afford(PROTOSSGROUNDARMORSLEVEL3) and self.armor_3 == False and self.units(TWILIGHTCOUNCIL).ready.amount >= 1:
					await self.do(forge.research(PROTOSSGROUNDARMORSLEVEL3))
					self.armor_3 = True	

	async def do_tc_research(self):
		if self.charge == True:
			return

		t_councils = self.units(TWILIGHTCOUNCIL).ready.noqueue
		if not t_councils.exists:
			return

		tc = t_councils.first
		if tc is not None:
			if self.charge == False and self.can_afford(CHARGE):
				await self.do(tc.research(CHARGE))
				self.charge = True		



#runs the actual game
run_game(maps.get("AbyssalReefLE"), [
	#Human(Race.Terran),
	Bot(Race.Protoss, ZealotRushBot()),
	Computer(Race.Random, Difficulty.Hard)
	], realtime=False)