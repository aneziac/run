import pygame as pg
import math


class Player:
    def __init__(self):
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = 30


class World:
    def __init__(self, color, verts):
        self.world_color = color
        self.polygon_verts = verts

        self.log_base = 2
        self.vanish_polygon_radius = 0

        self.render_distance = 15
        self.back_render_distance = 2

        self.create_map(50)
        self.create_lines()

    def create_lines(self):
        self.vanish_length = ((SCREEN_HEIGHT / 2) / math.cos(math.pi / self.polygon_verts)) - self.vanish_polygon_radius
        self.line_scale = self.vanish_length / math.log(self.render_distance - self.back_render_distance, self.log_base)
        self.x_offset = round(SCREEN_WIDTH / 2 - ((SCREEN_HEIGHT / 2) * math.tan(math.pi / self.polygon_verts)))
        self.polygon_ang = 2 * math.pi / self.polygon_verts

    def create_map(self, world_depth):
        self.world_map = [[1] * self.polygon_verts for _ in range(world_depth)]
        self.world_map = self.world_map + [[0] * self.polygon_verts for _ in range(2 * self.render_distance)]

        self.world_map[13][0] = 0

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

        projected_verts[:self.back_render_distance] = projected_verts[self.back_render_distance::-1]

        return projected_verts


class Game:
    def __init__(self):
        pg.init()
        self.running = True
        self.screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        self.depth = 1

        self.player = Player()
        self.world = World([0, 255, 0], 6)

        self.game_loop()

    def game_loop(self):
        while self.running:
            keys = pg.key.get_pressed()
            if pg.QUIT in [event.type for event in pg.event.get()] or keys[pg.K_ESCAPE]:
                self.running = False

            self.screen.fill([0] * 3)
            projected_verts = self.world.project_vertices(self.depth)

            self.render_world(projected_verts)
            self.depth += 0.05

            pg.display.update()

    @staticmethod
    def rotate(coords, theta):
        x, y = coords
        tx, ty = x - (SCREEN_WIDTH // 2), y - (SCREEN_HEIGHT // 2)
        rx, ry = round(tx * math.cos(theta) - ty * math.sin(theta)), round(tx * math.sin(theta) + ty * math.cos(theta))
        return [rx + (SCREEN_WIDTH // 2), ry + (SCREEN_HEIGHT // 2) - 50]

    def render_world(self, projected_verts):
        def build(x, v):
            return [Game.rotate(projected_verts[x], self.world.polygon_ang * v)]

        # draw projected vertices
        for x in range(self.world.render_distance + self.world.back_render_distance - 1):
            for v in range(self.world.polygon_verts):
                if self.world.world_map[x + math.floor(self.depth)][v] == 1:
                    pg.draw.polygon(self.screen, [0, 255 - x * 10, 0], build(x, v) + build(x + 1, v) + build(x + 1, v + 1) + build(x, v + 1))


if __name__ == '__main__':
    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
    game = Game()
