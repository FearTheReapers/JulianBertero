import sc2
import random

from sc2.constants import *
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.helpers import ControlGroup
from sc2.position import Pointlike, Point2, Point3
from sc2.units import Units
from sc2.unit import Unit

class BoomBot(sc2.BotAI):
    # A bot who will soon learn how to bounce noobs around forever
    def __init__(self):
        self.Chaining = False               # If Chaining Grenades
        self.Spot = Pointlike((30, 30))
        self.Destinaton = Point2(self.Spot) # Where we initially move to
        self.Bomb = Pointlike((32, 32))
        self.Target = Point2(self.Bomb)     # Where initial bomb lands

        self.cg = ()                        # Control Groups

        self.SCV_counter = 0                # Base Building
        self.refinerys = 0
        self.barracks_started = False
        self.made_workers_for_gas = False
        self.attack_groups = set()
        self.Ideal_Workers = False

    async def on_step(self, iteration):

        current_state = [
            enemy_units,
            available_reapers,
            cooldown_reapers,
        ]


        if iteration == 0:
            if iteration == 0:
                await self.chat_send("(glhf)")

#creates control groups of 14 reapers
        if self.units(REAPER).idle.amount > 14:
            cg = ControlGroup(self.units(REAPER).idle)
            self.attack_groups.add(cg)

# trains workers
        for cc in self.units(UnitTypeId.COMMANDCENTER).ready.noqueue:
            if self.can_afford(SCV) and self.workers.amount < 20 and cc.noqueue:
                await self.do(cc.train(SCV))

        cc = self.units(COMMANDCENTER).ready.first
        bobthebuilder = self.units(SCV)[0]

#build supply depots
        if self.supply_left < 2:
            if self.can_afford(SUPPLYDEPOT) and self.already_pending(SUPPLYDEPOT) < 2:
                await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))

#build barracks
        if self.units(BARRACKS).amount < 3 or (self.minerals > 400 and self.units(BARRACKS).amount < 5):
            if self.can_afford(BARRACKS):
                err = await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 5))
#train reapers
        elif self.units(BARRACKS).ready.exists and self.units(REFINERY).ready.exists:
            barracks = self.units(BARRACKS).ready
            if self.can_afford(REAPER) and barracks.noqueue:
                await self.do(barracks.random.train(REAPER))
#build refinerys
        if self.refinerys < 2:
            if self.can_afford(REFINERY):
                worker = self.workers.random
                target = self.state.vespene_geyser.closest_to(worker.position)
                err = await self.do(bobthebuilder.build(REFINERY, target))
                if not err:
                    self.refinerys += 1
#workers in the mines/gas
        for a in self.units(REFINERY):
            if a.assigned_harvesters < a.ideal_harvesters:
                w = self.workers.closer_than(20, a)
                if w.exists:
                    await self.do(w.random.gather(a))
            # elif a.assigned_harvesters > a.ideal_harvesters:
            #     b = self.units(MINERALFIELD)
            #     scrub = a.assigned_harvesters[0]
            #     await self.do(scrub.gather(b))
#send out reapers
        if self.units(REAPER).idle.amount > 14:
            # cg = ControlGroup(self.units(REAPER).idle)
            for reaper in self.units(REAPER):
                randx = random.random() * 100
                randy = random.random() * 100
                cluster = Pointlike((30+(randx/10), 30+(randy/10)))
                chill = Point2(cluster)
                await self.do(reaper.move(chill))
                # abilities = await self.get_available_abilities(reaper)
                # if AbilityId.HOLDPOSITION in abilities:
                #     await self.do(reaper(HOLDPOSITION, self.Destinaton))
#begin chaining, currently off
        if self.Chaining == True:
            for reaper in cg:
                abilities = await self.get_available_abilities(reaper)
                if AbilityId.KD8CHARGE_KD8CHARGE in abilities:
                    await self.do(reaper(KD8CHARGE_KD8CHARGE, self.Target))


class NoobNoob(sc2.BotAI):
    # NoobNoob is a worker whos fate is to be tossed around by enemy reapers
    def __init__(self):
        self.point = Pointlike((20,20))
        self.nextpoint = Point2(self.point)    #where we send our noobs
        self.workers = 12
        self.noob = False                    #keep count of noobs


    async def on_step(self, iteration):

            # SEND INITIAL NOOB
        if iteration == 0:
            noob = self.workers[0]
            await self.do(noob.move(self.nextpoint))

            # SET RALLY POINT FOR NOOB CENTER
        for cc in self.units(COMMANDCENTER):
            abilities = await self.get_available_abilities(cc)
            if AbilityId.RALLY_COMMANDCENTER in abilities:
                await self.do(cc(RALLY_COMMANDCENTER, self.nextpoint))
            # WHEN NOOB DIES, SPAWN NEW NOOB
        for cc in self.units(UnitTypeId.COMMANDCENTER).ready.noqueue:
            if cc.assigned_harvesters < 12:
                await self.do(cc.train(SCV))








#start the game
run_game(maps.get("Simple64"), [
    Bot(Race.Terran, NoobNoob()),
    Bot(Race.Terran, BoomBot())
], realtime=False)
