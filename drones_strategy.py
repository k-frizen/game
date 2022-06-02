# -*- coding: utf-8 -*-
import random
from collections import defaultdict
from typing import List, Union

import numpy
from astrobox.core import Drone, Asteroid, MotherShip
from robogame_engine.geometry import Point

CLOSEST = 0
FAR = 1
RANDOM = 2


class MyDrone(Drone):
    """Class of unit team MyDrone """
    payload_stat = defaultdict(int)

    def __init__(self):
        super().__init__()
        self.valid_asteroids = []

    def on_born(self):
        """Drone's actions when it born: drone fly to closest asteroid"""
        self.target = self.get_asteroid(CLOSEST)
        self.move_at(self.target)

    def move_at(self, target, speed=None):
        """Drone's actions when it move to target

        :param target: final point or object of the way
        :param speed: represents how fast drone will be move to target"""
        self.collect_stat(target)
        super().move_at(target)

    def on_stop_at_asteroid(self, asteroid: Asteroid):
        """Drone's actions in case of stop at asteroid

        :param asteroid: Asteroid class game object"""
        self.valid_asteroids = self.current_valid_asteroids()
        if self.free_space <= asteroid.payload or not self.valid_asteroids:
            self.turn_to(self.mothership)
        else:
            self.turn_to(self.get_asteroid(CLOSEST))

        if asteroid.payload:
            self.load_from(asteroid)
        elif self.payload:
            self.target = self.get_asteroid(CLOSEST) if self.valid_asteroids else self.mothership
            self.move_at(self.target)
        elif all(ast.is_empty for ast in self.asteroids) and self.is_empty:
            self.stop()
            self.stater()
        else:
            self.move_at(self.mothership)

    def on_load_complete(self):
        """Drone's actions after load elerium is complete"""
        self.valid_asteroids = self.current_valid_asteroids()

        if self.is_full or not self.valid_asteroids:
            self.target = self.mothership
        elif self.valid_asteroids:
            self.target = self.get_asteroid(CLOSEST)
        else:
            self.target = self.mothership

        self.move_at(self.target)

    def on_stop_at_mothership(self, mothership: MotherShip):
        """Drone's actions after stop on the base

        :param mothership: MotherShip's class game object, represents the base of drones"""
        self.unload_to(mothership)
        if self.current_valid_asteroids():
            # Drone turn to random asteroid on the scene because at this moment impossible to know next target.
            self.turn_to(self.get_asteroid(RANDOM))

    def on_unload_complete(self):
        """Drone's actions after unload elerium to base is complete"""
        self.valid_asteroids = self.current_valid_asteroids()
        if self.valid_asteroids:
            if len(self.valid_asteroids) > 1:
                half_of_valid_asteroids = self.half_asteroids(self.valid_asteroids)
                self.target = self.ast_with_max_payload(half_of_valid_asteroids)
            else:
                self.target = self.valid_asteroids[0]
            self.move_at(self.target)

        else:
            self.stop()
            self.stater()

    def current_valid_asteroids(self) -> List[Asteroid]:
        """Returns list of asteroids with any elerium and doesnt whether target for anyone in teammates

        :return: asteroids valid to accept drones at current time"""
        return [ast for ast in self.asteroids if not self.is_any_target(ast) and ast.payload]

    def half_asteroids(self, asteroids: list) -> List[Asteroid]:
        """Return list of half closest asteroids

        :param asteroids: asteroids for division
        :return: half closest asteroid to drone"""
        distances = tuple(self.distance_to(ast) for ast in asteroids)
        if len(distances) > 1:
            return [asteroids[distances.index(dist)] for dist in distances
                    if dist <= numpy.median(distances)]
        else:
            return asteroids

    def get_asteroid(self, dist: int) -> Asteroid:
        """Return random, closest or farthest asteroid

        :param dist: constant, determines random, closest or farthest asteroid will be returned
        :return: one of asteroids with payload > 0"""
        self.valid_asteroids = self.current_valid_asteroids()
        distances = [self.distance_to(ast) for ast in self.valid_asteroids]

        if dist == FAR:
            max_dist = distances.index(max(distances))
            return self.valid_asteroids[max_dist]

        elif dist == CLOSEST:
            min_dist = distances.index(min(distances))
            return self.valid_asteroids[min_dist]

        elif dist == RANDOM:
            return random.choice(self.valid_asteroids)

    @staticmethod
    def ast_with_max_payload(asteroids: list[Asteroid]) -> Asteroid:
        """Calculate asteroid with most payload from list of asteroids

        :param asteroids: analysed asteroids
        :return: asteroid with most payload from given asteroids"""
        payloads = [ast.payload for ast in asteroids]
        return asteroids[payloads.index(max(payloads))]

    def is_any_target(self, ast: Asteroid) -> bool:
        """Check whether this asteroid for anyone in teammates

        :param ast: asteroid to check
        :return: True if exist drone in teammates has ast as target"""
        return any(ast == mate.target for mate in self.teammates)

    def collect_stat(self, target: Union[MotherShip, Asteroid, Point]):
        """Collect distances to dictionary depends of payload

        :param target: final point or object of the way"""
        if self.is_full:
            key = 'full'
        elif self.is_empty:
            key = 'empty'
        elif self.payload < 50:
            key = '< half-load'
        else:
            key = '> half-load'
        self.payload_stat[key] += self.distance_to(target)

    def stater(self):
        """Prints statistic in view: fullness - percent of total distance covered"""
        if all(mate.is_empty for mate in self.teammates):
            total_dist = sum(self.payload_stat.values())

            for fullness, dist in self.payload_stat.items():
                percent = round(100 * dist / total_dist, 2)
                print(f'Drones have flown {fullness} {percent}% of game')
