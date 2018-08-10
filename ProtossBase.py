import sc2
import random

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.data import race_townhalls

class ProtossBaseBot(sc2.BotAI):
	##How can I make this work? I want to choose a random one of these and save them in a variable. At the start of the game
	#self.unit_focus = "BASIC_UNITS" | "DARK_TEMPLAR" | "AIR" | "ROBOTICS" | "PSI_STORM" 

	async def on_step(self, iteration):
		self.count += 1
		if(self.count > 50):
			await self.distribute_workers()  # in sc2/bot_ai.py
			self.count -= 50



		self.expand()
		self.train_probes()
		self.build_assimilators()
		#self.build_pylons() #pylons should be placed so that they are spread far enough to not overlap
		##Builds the main base. each building once early, twice later, and latergame even three times
		#self.build_main_base()
		##Build static defense around the main base. twice as much as on expansions (defenses: a chain of: pylon-> 3 photon cannons + 1 shield battery)
		#self.build_main_defenses()
		##Builds the expansion bases. each building once
		#self.build_expansion_bases()
		##Build static defense around the expansion bases. (defenses: a chain of: pylon-> 2 photon cannons)
		#self.build_expansions_defenses()
		#self.build_army()
		#self.research_tech()
		##only attack if 200 / 200
		#self.attack()
		##defend each base
		#self.defend()
		##have some units at each expansion, and more at the main base
		#self.split_army()
		##use observers to scout the borders
		#self.scout_borders()
		##surrender if out of pylons or main base nexus is destroyed
		#self.check_surrender()






	#async def check_surrender(self):
		#if not self.units(PYLON).ready.exists or  [check if main nexus has been destroyed]:
			#surrender			

	async def train_probes(self):
		maxProbes = self.townhalls.amount * 22
		if maxProbes > 76:
			maxProbes = 76

		if self.units(PROBE).amount < maxProbes:
			nexi = self.units(NEXUS).ready.noqueue
			if self.can_afford(PROBE) and nexi.exists and self.supply_left > 0:
				for nexus in nexi:
					await self.do(nexus.train(PROBE))

	async def expand(self):
		try:
			if self.can_afford(NEXUS) and not self.already_pending(NEXUS):
				#await self.chat_send('trying to expand')
				#library is not working; gotta wait for python-sc2 to fix that.
				#https://github.com/Dentosal/python-sc2/issues/97
				await self.expand_now()
		except AssertionError:
			print("AssertionError DAMNIT")

	async def build_assimilators(self):
		for nexus in self.townhalls.ready:
			vgs = self.state.vespene_geyser.closer_than(10, nexus)
			for vg in vgs:
				if not self.can_afford(ASSIMILATOR):
					break
				worker = self.select_build_worker(vg.position)
				if worker is None:
					break
				if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
					await self.do(worker.build(ASSIMILATOR, vg))







#runs the actualy game
run_game(maps.get("AbyssalReefLE"), [
	#Human(Race.Random),
	Bot(Race.Protoss, HiveMind()),
	Computer(Race.Terran, Difficulty.Easy)
	], realtime=False)