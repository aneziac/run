import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame as pg
from pygame import gfxdraw
import math
from random import random, randint


class Player(pg.sprite.Sprite):
    def __init__(self, world):
        super().__init__()
        self.SPRITE = pg.transform.smoothscale(pg.image.load(os.path.join('assets', 'sprite.png')), (100, 100))

        self.world = world

        THRESHOLD = SCREEN_HEIGHT // 2 * math.tan(math.pi / self.world.POLYGON_VERTS)
        self.LEFT_THRESHOLD = SCREEN_WIDTH // 2 - THRESHOLD - self.SPRITE.get_width() // 2
        self.RIGHT_THRESHOLD = SCREEN_WIDTH // 2 + THRESHOLD - self.SPRITE.get_width() // 2

        self.counter = 0
        self.rotation = 0
        self.ROTATION_SPEED = 15

        self.xpos = SCREEN_WIDTH // 2 - self.SPRITE.get_width() // 2
        self.STRAFE_SPEED = 7

        self.RESTING_YPOS = SCREEN_HEIGHT - 110
        self.ypos = self.RESTING_YPOS
        self.YACC = -0.2
        self.yvel = 0

    def update(self, keys, depth):
        face = round(((self.rotation / (2 * math.pi)) * -self.world.POLYGON_VERTS)) % self.world.POLYGON_VERTS

        if self.ypos < self.RESTING_YPOS or self.world.world_map[round(depth) + 1][face] == 0 or self.ypos > self.RESTING_YPOS + 20:
            self.yvel += self.YACC
        elif keys[pg.K_w]:
            self.yvel = 8
        else:
            self.yvel = 0
        self.ypos -= self.yvel

        if self.ypos > SCREEN_HEIGHT + 20:
            print("You lost")
            quit()

        if keys[pg.K_a]:
            self.xpos -= self.STRAFE_SPEED
        if keys[pg.K_d]:
            self.xpos += self.STRAFE_SPEED

        if self.counter == 0:
            if self.xpos < self.LEFT_THRESHOLD or self.xpos > self.RIGHT_THRESHOLD:
                self.counter = -1
                self.direction = math.copysign(1, self.xpos - (SCREEN_WIDTH // 2))

        if self.counter < 0 and self.ypos >= self.RESTING_YPOS - 40:
            self.counter = self.ROTATION_SPEED
            self.ypos = self.RESTING_YPOS - 100
            self.xpos = SCREEN_WIDTH // 2 - (self.SPRITE.get_width() // 2)
        elif self.counter > 0:
            self.rotation += 2 * math.pi * self.direction / self.world.POLYGON_VERTS / self.ROTATION_SPEED
            self.counter -= 1


class World:
    def __init__(self, color, verts):
        self.WORLD_COLOR = color
        self.POLYGON_VERTS = verts

        self.LOG_BASE = 2
        self.VANISH_RADIUS = 10

        self.RENDER_DISTANCE = 15
        self.BACK_RENDER_DISTANCE = 2

        self.height_offset = 100

        self.create_map()
        self.create_lines()
        self.create_stars()

    def create_lines(self):
        self.VANISH_LENGTH = ((SCREEN_HEIGHT / 2) / math.cos(math.pi / self.POLYGON_VERTS)) - self.VANISH_RADIUS
        self.LINE_SCALE = self.VANISH_LENGTH / math.log(self.RENDER_DISTANCE - self.BACK_RENDER_DISTANCE, self.LOG_BASE)
        self.X_OFFSET = round(SCREEN_WIDTH / 2 - ((SCREEN_HEIGHT / 2) * math.tan(math.pi / self.POLYGON_VERTS)))
        self.CENTRAL_ANGLE = 2 * math.pi / self.POLYGON_VERTS

    def create_stars(self, amount=80):
        self.stars = []
        size = max(SCREEN_WIDTH, SCREEN_HEIGHT)
        for x in range(amount):
            self.stars.append([randint(0, SCREEN_WIDTH - 1), randint(0, SCREEN_HEIGHT - 1), randint(2, 4), randint(50, 255)])

    def create_map(self, safe_area=10, world_depth=100):
        self.world_map = [[1] * self.POLYGON_VERTS for _ in range(world_depth)]
        self.world_map = self.world_map + [[0] * self.POLYGON_VERTS for _ in range(2 * self.RENDER_DISTANCE)]

        for x in range(len(self.world_map) - safe_area):
            for y in range(self.POLYGON_VERTS):
                if random() > 0.6:
                    self.world_map[x + safe_area][y] = 0

    def project_vertices(self, depth):
        depth_offset = depth - math.floor(depth)
        projected_verts = []

        # calculate location of projected vertices
        for x in range(self.RENDER_DISTANCE + self.BACK_RENDER_DISTANCE):
            if x < self.BACK_RENDER_DISTANCE:
                proj_dist = self.LOG_BASE ** (x + depth_offset + 1) * -self.LINE_SCALE
            else:
                proj_dist = math.log(x - depth_offset + 1 - self.BACK_RENDER_DISTANCE, self.LOG_BASE) * self.LINE_SCALE

            projected_verts.append([round(proj_dist * math.sin(math.pi / self.POLYGON_VERTS)) + self.X_OFFSET, round(SCREEN_HEIGHT - (proj_dist * math.cos(math.pi / self.POLYGON_VERTS)))])

        projected_verts[:self.BACK_RENDER_DISTANCE - 1] = projected_verts[self.BACK_RENDER_DISTANCE - 1:0:-1]

        return projected_verts


class Game:
    def __init__(self):
        pg.init()
        pg.event.set_blocked(None)
        pg.event.set_allowed([pg.QUIT])
        self.game_clock = pg.time.Clock()

        self.running = True
        self.screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT], pg.DOUBLEBUF)
        self.screen.set_alpha(None)
        self.depth = 1
        self.GAME_SPEED = 0.05

        self.world = World([0, 255, 0], 8)
        self.player = Player(self.world)

        self.game_loop()

    def game_loop(self):
        while self.running:
            keys = pg.key.get_pressed()
            if len(pg.event.get()) > 0 or keys[pg.K_ESCAPE]:
                self.running = False

            self.screen.fill([0] * 3)

            projected_verts = self.world.project_vertices(self.depth)
            self.render_world(projected_verts)

            self.player.update(keys, self.depth)
            self.render_player()
            self.depth += self.GAME_SPEED

            self.game_clock.tick()
            pg.display.update()

    def render_world(self, projected_verts):
        def build(x, v):
            return [rotate(projected_verts[x], self.world.CENTRAL_ANGLE * (v - 1))]

        def rotate(coords, theta):
            theta += self.player.rotation
            x, y = coords
            tx, ty = x - (SCREEN_WIDTH // 2), y - (SCREEN_HEIGHT // 2)
            rx, ry = round(tx * math.cos(theta) - ty * math.sin(theta)), round(tx * math.sin(theta) + ty * math.cos(theta))
            return [rx + (SCREEN_WIDTH // 2), ry + (SCREEN_HEIGHT // 2) - self.world.height_offset]

        # draw stars
        for x in self.world.stars:
            self.draw_circle(rotate(x[:2], self.player.rotation), x[2], [x[3]] * 3)

        # draw projected vertices
        for x in range(self.world.RENDER_DISTANCE + self.world.BACK_RENDER_DISTANCE - 1):
            for v in range(self.world.POLYGON_VERTS):
                if self.world.world_map[x + math.floor(self.depth)][v] == 1:
                    color = [0, 255 - x * 15, 0]
                    vertices = build(x, v) + build(x + 1, v) + build(x + 1, v + 1) + build(x, v + 1)
                    self.draw_polygon(vertices, color)

        # draw vanishing point
        pg.draw.circle(self.screen, (0, 0, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - self.world.height_offset), self.world.VANISH_RADIUS)

    def render_player(self):
        self.screen.blit(self.player.SPRITE, (round(self.player.xpos), round(self.player.ypos)))

    def draw_polygon(self, vertices, color):
        pg.gfxdraw.aapolygon(self.screen, vertices, color)
        pg.gfxdraw.filled_polygon(self.screen, vertices, color)

    def draw_circle(self, coords, radius, color):
        if coords[0] + radius > 0 and coords[0] - radius < SCREEN_WIDTH and coords[1] + radius > 0 and coords[1] - radius < SCREEN_HEIGHT:
            pg.gfxdraw.aacircle(self.screen, coords[0], coords[1], radius, color)
            pg.gfxdraw.filled_circle(self.screen, coords[0], coords[1], radius, color)

    def is_onscreen(self, x, y=None):
        if y is None:
            x, y = x
        return x > 0 and x < SCREEN_WIDTH and y > 0 and y < SCREEN_HEIGHT


if __name__ == '__main__':
    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
    game = Game()
