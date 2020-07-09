import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame as pg
from pygame import gfxdraw
import math
import random


class Player(pg.sprite.Sprite):
    def __init__(self, polygon_verts, world_map):
        self.sprite = pg.transform.smoothscale(pg.image.load(os.path.join('assets', 'sprite.png')), (100, 100))
        self.xpos = SCREEN_WIDTH // 2 - self.sprite.get_width() // 2
        self.iypos = SCREEN_HEIGHT - 110

        self.polygon_verts = polygon_verts
        self.world_map = world_map

        threshold = SCREEN_HEIGHT // 2 * math.tan(math.pi / self.polygon_verts)
        self.left_threshold = SCREEN_WIDTH // 2 - threshold - (self.sprite.get_width() // 2)
        self.right_threshold = SCREEN_WIDTH // 2 + threshold - (self.sprite.get_width() // 2)

        self.counter = 0
        self.rotation = 0

        self.ypos = self.iypos
        self.yacc = -0.2
        self.yvel = 0

        self.rotation_speed = 15
        super().__init__()

    def update(self, keys, depth):
        face = round(((self.rotation / (2 * math.pi)) * -self.polygon_verts)) % self.polygon_verts

        if self.ypos < self.iypos or self.world_map[round(depth) + 1][face] == 0 or self.ypos > self.iypos + 20:
            self.yvel += self.yacc
        elif keys[pg.K_w]:
            self.yvel = 8
        else:
            self.yvel = 0
        self.ypos -= self.yvel

        if self.ypos > SCREEN_HEIGHT + 20:
            print("You lost")
            quit()

        if keys[pg.K_a]:
            self.xpos -= 7
        if keys[pg.K_d]:
            self.xpos += 7

        if self.counter == 0:
            if self.xpos < self.left_threshold:
                self.counter = -self.rotation_speed
                self.sign = -1
            elif self.xpos > self.right_threshold:
                self.counter = -self.rotation_speed
                self.sign = 1

        if self.counter < 0 and self.ypos >= self.iypos - 40:
            self.counter = self.rotation_speed
            self.ypos = self.iypos - 100
            self.xpos = SCREEN_WIDTH // 2 - (self.sprite.get_width() // 2)# - (self.sign * 50)
        elif self.counter > 0:
            self.rotation += 2 * self.sign * math.pi / self.polygon_verts / self.rotation_speed
            self.counter -= 1


class World:
    def __init__(self, color, verts):
        self.world_color = color
        self.polygon_verts = verts

        self.log_base = 2
        self.vanish_polygon_radius = 10

        self.render_distance = 15
        self.back_render_distance = 2

        self.height_offset = 100
        self.safe_area = 10

        self.create_map(100)
        self.create_lines()
        self.create_stars(80)

    def create_lines(self):
        self.vanish_length = ((SCREEN_HEIGHT / 2) / math.cos(math.pi / self.polygon_verts)) - self.vanish_polygon_radius
        self.line_scale = self.vanish_length / math.log(self.render_distance - self.back_render_distance, self.log_base)
        self.x_offset = round(SCREEN_WIDTH / 2 - ((SCREEN_HEIGHT / 2) * math.tan(math.pi / self.polygon_verts)))
        self.polygon_ang = 2 * math.pi / self.polygon_verts

    def create_stars(self, num):
        self.stars = []
        for x in range(num):
            self.stars.append([random.randint(0, SCREEN_WIDTH - 1), random.randint(0, SCREEN_HEIGHT - 1), random.randint(2, 4), random.randint(50, 255)])

    def create_map(self, world_depth):
        self.world_map = [[1] * self.polygon_verts for _ in range(world_depth)]
        self.world_map = self.world_map + [[0] * self.polygon_verts for _ in range(2 * self.render_distance)]

        for x in range(len(self.world_map) - self.safe_area):
            for y in range(self.polygon_verts):
                if random.random() > 0.6:
                    self.world_map[x + self.safe_area][y] = 0

    def project_vertices(self, depth):
        depth_offset = depth - math.floor(depth)
        projected_verts = []

        # calculate location of projected vertices
        for x in range(self.render_distance + self.back_render_distance):
            if x < self.back_render_distance:
                proj_dist = self.log_base ** (x + depth_offset + 1) * -self.line_scale
            else:
                proj_dist = math.log(x - depth_offset + 1 - self.back_render_distance, self.log_base) * self.line_scale

            projected_verts.append([round(proj_dist * math.sin(math.pi / self.polygon_verts)) + self.x_offset, round(SCREEN_HEIGHT - (proj_dist * math.cos(math.pi / self.polygon_verts)))])

        projected_verts[:self.back_render_distance - 1] = projected_verts[self.back_render_distance - 1:0:-1]

        return projected_verts


class Game:
    def __init__(self):
        pg.init()
        self.running = True
        self.screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        self.depth = 1
        self.game_speed = 0.05

        self.world = World([0, 255, 0], 8)
        self.player = Player(self.world.polygon_verts, self.world.world_map)

        self.game_loop()

    def game_loop(self):
        while self.running:
            keys = pg.key.get_pressed()
            if pg.QUIT in [event.type for event in pg.event.get()] or keys[pg.K_ESCAPE]:
                self.running = False

            self.screen.fill([0] * 3)

            projected_verts = self.world.project_vertices(self.depth)
            self.render_world(projected_verts)

            self.player.update(keys, self.depth)
            self.render_player()
            self.depth += self.game_speed

            pg.display.update()

    def render_world(self, projected_verts):
        def build(x, v):
            return [rotate(projected_verts[x], self.world.polygon_ang * (v - 1))]

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
        for x in range(self.world.render_distance + self.world.back_render_distance - 1):
            for v in range(self.world.polygon_verts):
                if self.world.world_map[x + math.floor(self.depth)][v] == 1:
                    color = [0, 255 - x * 15, 0]
                    vertices = build(x, v) + build(x + 1, v) + build(x + 1, v + 1) + build(x, v + 1)
                    self.draw_polygon(vertices, color)

        # draw vanishing point
        pg.draw.circle(self.screen, (0, 0, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - self.world.height_offset), self.world.vanish_polygon_radius)

    def render_player(self):
        self.screen.blit(self.player.sprite, (round(self.player.xpos), round(self.player.ypos)))

    def draw_polygon(self, vertices, color):
        pg.gfxdraw.aapolygon(self.screen, vertices, color)
        pg.gfxdraw.filled_polygon(self.screen, vertices, color)

    def draw_circle(self, coords, radius, color):
        pg.gfxdraw.aacircle(self.screen, coords[0], coords[1], radius, color)
        pg.gfxdraw.filled_circle(self.screen, coords[0], coords[1], radius, color)

if __name__ == '__main__':
    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
    game = Game()
