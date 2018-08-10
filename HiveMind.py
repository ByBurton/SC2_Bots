import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls
#from terran import BotName

class HiveMind(sc2.BotAI):
	async def on_step(self, iteration):
		self.count += 1
		if(self.count > 50):
			await self.distribute_workers()  # in sc2/bot_ai.py
			self.count -= 50
		await self.maintain_enough_control()
		await self.build_drones()  # workers bc obviously
		await self.expand()
		await self.spawn_larvae()
		await self.move_overlords()
		await self.get_queens()
		await self.extractors()
		await self.build_spawning_pools()
		await self.build_army()
		await self.build_evolution_chambers()
		await self.build_hydralisk_dens()
		await self.build_spires()
		await self.build_infestation_pits()
		await self.build_ultralisk_caverns()
		#await self.build_defenses()
		await self.upgrade_hatcheries()
		await self.attack()
		await self.defend()

	async def extractors(self):
		for hatchery in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(10, hatchery)
			for vg in vgs:
				if not self.can_afford(EXTRACTOR):
					break
				worker = self.select_build_worker(vg.position)
				if worker is None:
					break
				if not self.units(EXTRACTOR).closer_than(1.0, vg).exists:
					await self.do(worker.build(EXTRACTOR, vg))

	async def build_drones(self):
		maxdrones = self.townhalls.amount * 22
		if maxdrones > 60:
			maxdrones = 70

		if self.units(DRONE).amount < maxdrones:
			larvae = self.units(LARVA)
			if self.can_afford(DRONE) and larvae.exists and self.supply_left > 0:
				larva = larvae.random
				await self.do(larva.train(DRONE))

	async def get_queens(self):
		if self.can_afford(QUEEN) and self.units(SPAWNINGPOOL).ready.exists and self.units(QUEEN).amount < self.townhalls.amount:
			hatcheries = self.townhalls.ready.noqueue
			if hatcheries.exists:
				for hatchery in hatcheries:
					if self.can_afford(QUEEN):
						await self.do(hatchery.train(QUEEN))


	async def spawn_larvae(self):
		for hatch in self.townhalls.ready:
			if not hatch.has_buff(QUEENSPAWNLARVATIMER) and self.units(QUEEN).exists:
				lucky = self.units(QUEEN).closest_to(hatch)
				abilities = await self.get_available_abilities(lucky)
				if AbilityId.EFFECT_INJECTLARVA in abilities and lucky.energy > 25:
					await self.do(lucky(EFFECT_INJECTLARVA, hatch))

	#move overlords around. "I see you! You can not hide."
	async def move_overlords(self):
		for overlord in self.units(OVERLORD).idle:
			hatcheries = self.townhalls.ready
			if hatcheries.exists:
				hatchery = hatcheries.random
				pos = hatchery.position.random_on_distance(21)
				await self.do(overlord.move(pos))

	#too many underlings
	async def maintain_enough_control(self):
		if self.units(OVERLORD).amount > 25 + self.townhalls.amount:
			return

		larvae = self.units(LARVA)
		supply_hives = 5 * self.townhalls.amount
		if self.supply_left < supply_hives and self.can_afford(OVERLORD) and larvae.exists and not self.already_pending(OVERLORD):
			await self.do(larvae.random.train(OVERLORD))


	async def build_spawning_pools(self):
		for hatchery in self.townhalls.ready:
			if self.townhalls.exists and self.can_afford(SPAWNINGPOOL) and not self.already_pending(SPAWNINGPOOL):
				spools = self.units(SPAWNINGPOOL).closer_than(20, hatchery.position)
				if not spools.exists:
					await self.build(SPAWNINGPOOL, near=hatchery.position)

	async def build_evolution_chambers(self):
		for hatchery in self.townhalls.ready:
			if self.can_afford(EVOLUTIONCHAMBER) and self.townhalls.exists and not self.already_pending(EVOLUTIONCHAMBER) and self.units(SPAWNINGPOOL).exists:
				chambers = self.units(EVOLUTIONCHAMBER).closer_than(20, hatchery.position)
				if not chambers.exists:
					await self.build(EVOLUTIONCHAMBER, near=hatchery.position)

	async def build_hydralisk_dens(self):
		for hatchery in self.townhalls.ready:
			if self.units(LAIR).exists or self.units(HIVE).exists:
				if self.can_afford(HYDRALISKDEN) and self.townhalls.exists and self.units(SPAWNINGPOOL).exists and not self.already_pending(HYDRALISKDEN):
					dens = self.units(HYDRALISKDEN).closer_than(20, hatchery.position)
					if not dens.exists:
						await self.build(HYDRALISKDEN, near=hatchery.position)

	async def build_spires(self):
		for hatchery in self.townhalls.ready:
			if self.units(LAIR).exists or self.units(HIVE).exists:
				if self.can_afford(SPIRE) and self.units(SPAWNINGPOOL).exists and not self.already_pending(SPIRE):
					spires = self.units(SPIRE).closer_than(20, hatchery.position)
					if not spires.exists:
						await self.build(SPIRE, near=hatchery.position)

	async def build_infestation_pits(self):
		for hatchery in self.townhalls.ready:
			if self.units(LAIR).exists or self.units(HIVE).exists:
				if self.can_afford(INFESTATIONPIT) and self.units(SPAWNINGPOOL).exists and not self.already_pending(INFESTATIONPIT):
					pits = self.units(INFESTATIONPIT).closer_than(20, hatchery.position)
					if not pits.exists:
						await self.build(INFESTATIONPIT, near=hatchery.position)

	async def build_ultralisk_caverns(self):
		for hatchery in self.townhalls.ready:
			if self.units(HIVE).exists:
				if self.can_afford(ULTRALISKCAVERN) and self.units(SPAWNINGPOOL).exists and not self.already_pending(ULTRALISKCAVERN):
					caverns = self.units(ULTRALISKCAVERN).closer_than(20, hatchery.position)
					if not caverns.exists:
						await self.build(ULTRALISKCAVERN, near=hatchery.position)

	#upgrade all our bases. we are the swarm
	async def upgrade_hatcheries(self):
		for hatchery in self.units(HATCHERY).ready.noqueue:
			if self.can_afford(LAIR) and self.units(SPAWNINGPOOL).ready.exists:
				await self.do(hatchery.build(LAIR))
		for tier2 in self.units(LAIR).ready.noqueue:
			if self.can_afford(HIVE) and self.units(INFESTATIONPIT).ready.exists:
				await self.do(tier2.build(HIVE))

	def find_target(self, state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units).position
		elif len(self.known_enemy_structures):
			return random.choice(self.known_enemy_structures).position
		else:
			return self.enemy_start_locations[0]

	#build me an army worthy of mordor
	async def build_army(self):
		ultralisks = 3 #18 supply
		mutalisks = 13 #26 supply
		hydralisks = 24 #48 supply
		zerglings = 60 #30 supply
		#needed supply 122

		if self.units(DRONE).amount > 70:
			count = self.units(DRONE).amount - 70
			currentCount = count

			for drone in self.units(DRONE):
				if count > 0:
					await self.do(drone.attack(self.find_target(self.state)))
					count = count - 1
					self.chat_send('suiciding drone(s)')
					break


		#if self.units(DRONE).amount < 15 * self.townhalls.ready.amount:
			#return

		if self.can_afford(ULTRALISK) and self.units(ULTRALISKCAVERN).ready.exists and self.units(ULTRALISK).amount < ultralisks and self.supply_left > 6:
			larvae = self.units(LARVA)
			if larvae.exists:
				larva = larvae.random
				await self.do(larva.train(ULTRALISK))
		if self.can_afford(MUTALISK) and self.units(SPIRE).ready.exists and self.units(MUTALISK).amount < mutalisks and self.supply_left > 2:
			larvae = self.units(LARVA)
			if larvae.exists:
				larva = larvae.random
				await self.do(larva.train(MUTALISK))
		if self.can_afford(HYDRALISK) and self.units(HYDRALISKDEN).ready.exists and self.units(HYDRALISK).amount < hydralisks and self.supply_left > 2:
			larvae = self.units(LARVA)
			if larvae.exists:
				larva = larvae.random
				await self.do(larva.train(HYDRALISK))
		if self.can_afford(ZERGLING) and self.units(SPAWNINGPOOL).ready.exists and self.units(ZERGLING).amount < zerglings and self.supply_left > 1:
			larvae = self.units(LARVA)
			if larvae.exists:
				larva = larvae.random
				await self.do(larva.train(ZERGLING))

	#attack with all the force we got, not earlier
	async def attack(self):
		if self.units(ZERGLING).amount > 59 and self.units(HYDRALISK).amount > 23 and self.units(MUTALISK).amount > 12 and self.units(ULTRALISK).amount > 2:
			forces = self.units(ZERGLING).idle | self.units(HYDRALISK).idle | self.units(MUTALISK).idle | self.units(ULTRALISK).idle
			self.gather_forces()

			self.chat_send('gg ez')
			for unit in forces.idle:
				await self.do(unit.attack(self.find_target(self.state)))

	#does not seem to work
	async def gather_forces(self):
		await self.chat_send('gathing forces')
		forces = self.units(ZERGLING).idle | self.units(HYDRALISK).idle | self.units(MUTALISK).idle | self.units(ULTRALISK).idle

		pos = self.townhalls.ready.random
		for unit in forces:
			await self.do(unit.move(pos))

	#base defense
	#todo: do not follow the enemy back to their base
	async def defend(self):
		forces = self.units(ZERGLING).idle | self.units(HYDRALISK).idle | self.units(MUTALISK).idle | self.units(ULTRALISK).idle
		self.gather_forces()

		for building in self.units().structure:
			bl_pos = building.position
			for unit in forces:
				if self.known_enemy_units.closer_than(10, bl_pos).exists:
					choice = random.choice(self.known_enemy_units.closer_than(30, bl_pos))
					await self.do(unit.attack(choice.position))


	async def expand(self):
		try:
			if self.can_afford(HATCHERY) and not self.already_pending(HATCHERY):
				#await self.chat_send('trying to expand')
				#library is not working; gotta wait for python-sc2 to fix that.
				#https://github.com/Dentosal/python-sc2/issues/97
				await self.expand_now()
		except AssertionError:
			print("AssertionError DAMNIT")

	#async def upgrades(self):
		#if self.minerals > 750 and self.vespene > 325:




#runs the actualy game
run_game(maps.get("AbyssalReefLE"), [
	#Human(Race.Random),
	Bot(Race.Zerg, HiveMind()),
	Computer(Race.Terran, Difficulty.Easy)
	], realtime=False)