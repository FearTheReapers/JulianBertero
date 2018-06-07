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
        self.Spot = Pointlike((23, 23))
        self.Destination = Point2(self.Spot) # Where we initially move to
        self.Bomb = Pointlike((20, 20))
        self.Target = Point2(self.Bomb)     # Where initial bomb lands

        # state
        self.Enemy_Units = ()
        self.Available_Reapers = ()
        self.Cooldown_Reapers = ()

        self.cg = ()                        # Control Groups

        self.SCV_counter = 0                # Base Building
        self.refinerys = 0
        self.barracks_started = False
        self.made_workers_for_gas = False
        self.attack_groups = set()
        self.Ideal_Workers = False


    # async def aim(self, Target):
    #     x = Target.x - .5
    #     y = Target.y - .5
    #     rand = random.random() * 100
    #     randx = (rand/100) + x
    #     rand = random.random() * 100
    #     randy = (rand/100) + y
    #     boom = Pointlike((randx, randy))
    #     return Point2(boom)

    async def on_step(self, iteration):



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
        if self.units(BARRACKS).amount < 1: # or (self.minerals > 400 and self.units(BARRACKS).amount < 5):
            if self.can_afford(BARRACKS):
                err = await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 5))
#train reapers
        elif self.units(BARRACKS).ready.exists and self.units(REFINERY).ready.exists and self.units(REAPER).amount < 1:
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

#send out reapers
        # if self.units(REAPER).idle.amount > 14:
        #     # cg = ControlGroup(self.units(REAPER).idle)
        #     for reaper in self.units(REAPER):
        #         randx = random.random() * 100
        #         randy = random.random() * 100
        #         cluster = Pointlike((30+(randx/10), 30+(randy/10)))
        #         chill = Point2(cluster)
        #         await self.do(reaper.move(chill))
                # abilities = await self.get_available_abilities(reaper)
                # if AbilityId.HOLDPOSITION in abilities:
                #     await self.do(reaper(HOLDPOSITION, self.Destinaton))
#begin chaining, currently off


        if self.units(REAPER).amount > 0:
            for reaper in self.units(REAPER).idle:
                if reaper == self.units(REAPER).first:
                    # if self.units(SCV).enemy:
                    #     await self.do(reaper.move(self.Destination))
                # if reaper.position
            # nade at enemy
                    if self.units(SCV).enemy.amount > 0:
                        for worker in self.units(SCV).enemy:
                            print(worker.position)
                        # enemy = self.Units.is_enemy.first
                        # target = enemy.position
                        # abilities = await self.get_available_abilities(reaper)
                        # if AbilityId.KD8CHARGE_KD8CHARGE in abilities:
                        #     await self.do(reaper(KD8CHARGE_KD8CHARGE, target))
                # nade at default
                    else:
                        for reaper in self.units(REAPER).owned:
                            print(reaper.position)
                            await self.do(reaper.move(self.Destination))
                        # target = self.Destination
                        # abilities = await self.get_available_abilities(reaper)
                        # if AbilityId.KD8CHARGE_KD8CHARGE in abilities:
                        #     await self.do(reaper.move(target))
                # else:
                #     await self.do(reaper(STOP, self.Target))
        # if self.units(REAPER).idle.amount > 0 and :
        #     reaper = self.units(REAPER).idle.first
        #     abilities = await self.get_available_abilities(reaper)
        #     # lz = self.aim(self.Target)
        #
        #     x = self.Target.x - .5
        #     y = self.Target.y - .5
        #     rand = random.random() * 100
        #     randx = (rand/100) + x
        #     rand = random.random() * 100
        #     randy = (rand/100) + y
        #     boom = Pointlike((randx, randy))
        #     lz = Point2(boom)
        #
        #
        #     if AbilityId.KD8CHARGE_KD8CHARGE in abilities:
        #         await self.do(reaper(KD8CHARGE_KD8CHARGE, lz))
        #         await self.do(reaper.move(self.Destination))

        # smart_actions = [KD8CHARGE_KD8CHARGE]


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
            # MOAR NOOBS
        if self.supply_left < 2:
            if self.can_afford(SUPPLYDEPOT) and self.already_pending(SUPPLYDEPOT) < 2:
                await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))
# Stolen from https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow
class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)

        if np.random.uniform() < self.epsilon:
            # choose best action
            state_action = self.q_table.ix[observation, :]

            # some actions have the same value
            state_action = state_action.reindex(np.random.permutation(state_action.index))

            action = state_action.idxmax()
        else:
            # choose random action
            action = np.random.choice(self.actions)

        return action

    def learn(self, s, a, r, s_):
        self.check_state_exist(s_)
        self.check_state_exist(s)

        q_predict = self.q_table.ix[s, a]
        q_target = r + self.gamma * self.q_table.ix[s_, :].max()

        # update
        self.q_table.ix[s, a] += self.lr * (q_target - q_predict)

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))





#start the game
run_game(maps.get("Simple64"), [
    Bot(Race.Terran, NoobNoob()),
    Bot(Race.Terran, BoomBot())
], realtime=False)
