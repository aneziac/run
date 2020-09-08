import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame as pg
from pygame import gfxdraw
import math
import time
from random import random, randint
import sys


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

        self.RESTING_XPOS = SCREEN_WIDTH // 2 - self.SPRITE.get_width() // 2
        self.xpos = self.RESTING_XPOS
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
            return True

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
            self.xpos = self.RESTING_XPOS
        elif self.counter > 0:
            self.rotation += 2 * math.pi * self.direction / self.world.POLYGON_VERTS / self.ROTATION_SPEED
            self.counter -= 1


class World:
    def __init__(self, level):
        self.WORLD_COLOR = [randint(0, 100), randint(100, 255), randint(100, 255)]
        self.POLYGON_VERTS = randint(4, 10)

        self.LOG_BASE = 2
        self.VANISH_RADIUS = 10

        self.RENDER_DISTANCE = 15
        self.BACK_RENDER_DISTANCE = 2
        self.WORLD_DEPTH = randint(level * 5 + 20, level * 6 + 30)

        self.height_offset = 100

        self.create_map(world_depth=self.WORLD_DEPTH)
        self.create_lines()
        self.create_stars()

    def create_lines(self):
        self.VANISH_LENGTH = ((SCREEN_HEIGHT / 2) / math.cos(math.pi / self.POLYGON_VERTS)) - self.VANISH_RADIUS
        self.LINE_SCALE = self.VANISH_LENGTH / math.log(self.RENDER_DISTANCE - self.BACK_RENDER_DISTANCE, self.LOG_BASE)
        self.X_OFFSET = round(SCREEN_WIDTH / 2 - ((SCREEN_HEIGHT / 2) * math.tan(math.pi / self.POLYGON_VERTS)))
        self.CENTRAL_ANGLE = 2 * math.pi / self.POLYGON_VERTS

    def create_stars(self, amount=250):
        self.stars = []
        size = max(SCREEN_WIDTH, SCREEN_HEIGHT)
        for x in range(amount):
            self.stars.append([randint(-200, size - 1), randint(-200, size - 1), randint(1, 2), randint(100, 255)])

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
        pg.font.init()
        pg.event.set_blocked(None)
        pg.event.set_allowed([pg.QUIT])
        self.game_clock = pg.time.Clock()
        self.font = pg.font.Font("assets/font/retro.ttf", 100)
        self.small_font = pg.font.Font("assets/font/retro.ttf", 30)
        pg.mouse.set_visible(False)

        self.wait = False
        self.last_time = time.time()
        self.running = True
        self.title = True

        flags = pg.DOUBLEBUF | pg.FULLSCREEN
        if len(sys.argv) > 1:
            if "w" in sys.argv[1]:
                flags = pg.DOUBLEBUF
        self.screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT], flags)
        self.screen.set_alpha(None)

        self.depth = 1
        self.GAME_SPEED = 0.05
        self.life = 1
        self.level = 1

        self.next_level()
        self.game_loop()

    def next_level(self):
        self.world = World(self.level)
        self.player = Player(self.world)

    def game_loop(self):
        while self.running:
            keys = pg.key.get_pressed()
            if len(pg.event.get()) > 0 or keys[pg.K_ESCAPE]:
                self.running = False
            if keys[pg.K_SPACE]:
                self.title = False

            self.screen.fill([0] * 3)

            projected_verts = self.world.project_vertices(self.depth)
            self.render_world(projected_verts)

            self.render_player()
            if self.depth > self.world.WORLD_DEPTH:
                self.level += 1
                self.reset()
                self.next_level()

            if self.wait:
                if time.time() - self.last_time > 2:
                    self.wait = False
                    self.reset(clock=False)
                elif self.depth == 1:
                    self.render_text("Level " + str(self.level))
                else:
                    self.render_text("You fell!")

            if self.title:
                self.render_text("Run!")
                self.render_text("Press space", location=[SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70], font=self.small_font)
            elif not self.wait:
                if self.depth < 6:
                    self.render_text("Life " + str(self.life))
                if self.player.update(keys, self.depth):
                    self.reset(position=False)
                    self.life += 1

                self.depth += self.GAME_SPEED
                self.game_clock.tick()

            pg.display.update()

    def reset(self, position=True, clock=True):
        if position:
            self.depth = 1
            self.player.xpos = self.player.RESTING_XPOS
            self.player.ypos = self.player.RESTING_YPOS
        if clock:
            self.wait = True
            self.last_time = time.time()

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
                    color = [max(0, self.world.WORLD_COLOR[y] - x * 12) for y in range(3)]
                    vertices = build(x, v) + build(x + 1, v) + build(x + 1, v + 1) + build(x, v + 1)
                    self.draw_polygon(vertices, color)

        # draw vanishing point
        self.draw_circle([SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - self.world.height_offset], self.world.VANISH_RADIUS, (0, 0, 0))

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

    def render_text(self, text, location=None, color=[100, 0, 0], font=None):
        if not location:
            location = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
        if not font:
            font = self.font
        rendered_text = font.render(text, True, color)
        location = [location[x] - (font.size(text)[x] // 2) for x in range(len(location))]
        self.screen.blit(rendered_text, location)


if __name__ == '__main__':
    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
    Game()
