import sc2
import random
import math

import numpy as np
import pandas as pd

from sc2.constants import *
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.helpers import ControlGroup
from sc2.position import Pointlike, Point2, Point3
from sc2.units import Units
from sc2.unit import Unit


ACTION_DO_NOTHING = 'donothing'
ACTION_KD8_CHARGE = 'kd8charge'

smart_actions = [
    ACTION_DO_NOTHING,
    ACTION_KD8_CHARGE,
]


class BoomBot(sc2.BotAI):
    # A bot who will soon learn how to bounce noobs around forever
    def __init__(self):
                                            # Reinforcement Learner
        self.qlearn = QLearningTable(actions=list(range(len(smart_actions))))
                                            # State
        self.prev_score = 0
        self.prev_action = None
        self.prev_state = None

        self.SCV_counter = 0                # Base Building
        self.refinerys = 0
        self.barracks_started = False
        self.made_workers_for_gas = False
        self.attack_groups = set()
        self.Ideal_Workers = False

# Old, potentially useful

        # self.Chaining = False               # If Chaining Grenades
        # self.Spot = Pointlike((23, 23))
        # self.Destination = Point2(self.Spot) # Where we initially move to
        # self.Bomb = Pointlike((20, 20))
        # self.Target = Point2(self.Bomb)     # Where initial bomb lands

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

        Available_Reapers = []
        Cooldown_Reapers = []
        Enemy_Units = []


        for reaper in self.units(REAPER):
            abilities = await self.get_available_abilities(reaper)
            if AbilityId.KD8CHARGE_KD8CHARGE in abilities:
                Available_Reapers.append(reaper)
            else:
                Cooldown_Reapers.append(reaper)
        for worker in self.units.enemy:
            if worker.is_enemy == True:
                Enemy_Units.append(worker)

        print(len(Enemy_Units))
        current_state = [
            Available_Reapers,
            Cooldown_Reapers,
            Enemy_Units,
        ]
        reward = 0
        if self.prev_action != None:

            for worker in Enemy_Units:
                if worker.health < worker.health_max:
                    reward += (worker.health_max - worker.health)

            self.qlearn.learn(str(self.prev_state), self.prev_action, reward, str(current_state))

        rl_action = self.qlearn.choose_action(str(current_state))
        smart_action = smart_actions[rl_action]

        self.prev_score = reward
        self.prev_state = current_state
        self.prev_action = rl_action

        if smart_action == ACTION_DO_NOTHING:
            for reaper in self.units(REAPER):
                await self.do(reaper(STOP, reaper.position))

        if smart_action == ACTION_KD8_CHARGE:
            if len(Available_Reapers) > 0: #len(Enemy_Units) > 0 and
                targetx = random.randrange(0, 63)
                targety = random.randrange(0, 63)
                target = Pointlike((targetx, targety))
                bomb = Point2(target)
                reaper = Available_Reapers[0]
                await self.do(reaper(KD8CHARGE_KD8CHARGE, bomb))
            else:
                for reaper in Available_Reapers:
                    targetx = random.randrange(0, 63)
                    targety = random.randrange(0, 63)
                    target = Pointlike((targetx, targety))
                    moveto = Point2(target)
                    await self.do(reaper.move(moveto))


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


# From https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow
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
