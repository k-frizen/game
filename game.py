# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from drones_strategy import MyDrone
from driller import DrillerDrone

NUMBER_OF_DRONES = 5

if __name__ == '__main__':
    scene = SpaceField(
        speed=5,
        asteroids_count=20,
    )
    team_1 = [MyDrone() for _ in range(NUMBER_OF_DRONES)]
    team_2 = [DrillerDrone() for _ in range(NUMBER_OF_DRONES)]
    scene.go()

