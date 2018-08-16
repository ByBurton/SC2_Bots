import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls

class BunkerBot(sc2.BotAI):
	#def __init__(self):



	async def on_step(self, iteration):
		if round(self.time) % 6 == 0:
			await self.distribute_workers()  # in sc2/bot_ai.py	

		await self.train_scvs()
		await self.build_engineering_bay()
		await self.build_defensive_bunker()
		#await self.offensive_bunker()
		await self.fill_bunkers()
		await self.build_refineries()
		#await self.do_research_engineering_bay()
		await self.train_marines()
		await self.build_supply_depots()
		await self.expand()
		await self.build_barracks()


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
		if self.units(SCV).amount >= 60:
			return

		maxscvs = ( self.townhalls.ready.amount * 20 )
		if maxscvs >= 60:
			maxscvs = 60

		commandcenters = self.townhalls.ready.noqueue
		if commandcenters.exists:
			for cc in commandcenters:
				if self.can_afford(SCV) and self.supply_left >= 1 and self.units(SCV).amount < maxscvs:
					await self.do(cc.train(SCV))

	async def build_supply_depots(self):
		cc = self.townhalls.random

		if self.supply_left <= 5 and self.can_afford(SUPPLYDEPOT):
			await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, -15))

	async def build_barracks(self):
		#pos =self.game_info.map_center.towards(self.enemy_start_locations[0], 10)

		cc = self.townhalls.ready.first

		if self.units(BARRACKS).amount < 2 and self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
			await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 10))

	async def train_marines(self):
		racks = self.units(BARRACKS).ready.noqueue
		req_units = self.units(BUNKER).amount * 4
		if req_units < 4:
			req_units = 4


		if not racks.exists:
			return

		if self.units(MARINE).amount < req_units and self.supply_left >= 1:
			for rack in racks:
				if self.can_afford(MARINE):
					await self.do(rack.train(MARINE))


	async def build_engineering_bay(self):
		cc = self.townhalls.ready.first

		if self.units(ENGINEERINGBAY).amount < 1 and self.can_afford(ENGINEERINGBAY) and not self.already_pending(ENGINEERINGBAY):
			await self.build(ENGINEERINGBAY, near=cc.position.towards(self.game_info.map_center, 5))

	async def fill_bunkers(self):
		bunkers = self.units(BUNKER).ready
		marines = self.units(MARINE).idle


		if not marines.exists or not bunkers.exists:
			return


		if marines.amount < 4:
			return

		marines = marines.take(4)

		for bunker in bunkers:
			for marine in marines:
				if bunker.cargo_used < bunker.cargo_max:
					await self.do(marine(AbilityId.SMART, bunker))
				else:
					break


	async def build_defensive_bunker(self):
		cc = self.townhalls

		if self.units(MARINE).amount < 4:
			return

		if not cc.exists or not self.units(BARRACKS).ready.exists:
			return

		for base in cc:
			if not self.units(BUNKER).closer_than(5, base.position.towards(self.game_info.map_center, 5)).amount > 2:
				if self.can_afford(BUNKER) and not self.already_pending(BUNKER):
					await self.build(BUNKER, near=base.position.towards(self.game_info.map_center, 5))

	async def offensive_bunker(self):
		if not self.can_afford(BUNKER) or self.already_pending(BUNKER) or not self.units(BARRACKS).ready.exists:
			return

		for _ in range(20):
			pos = self.enemy_start_locations[0].towards(self.game_info.map_center, random.randrange(7, 30))
			r = await self.build(BUNKER, near=pos)
			if not r: # success
				break




#runs the actual game
#run_game(maps.get("AbyssalReefLE"), [
run_game(maps.get("BelShirVestigeLE"), [
	#Human(Race.Zerg),
	Bot(Race.Terran, BunkerBot()),
	Computer(Race.Zerg, Difficulty.VeryEasy)
	], realtime=False)