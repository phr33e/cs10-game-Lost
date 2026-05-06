import arcade
import random
import math

NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 720
TITLE = "20-Lane Runner"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

PLAYER_Y = 90
PLAYER_SIZE = LANE_WIDTH - 10

OBSTACLE_TYPES = [
    {"color": arcade.color.RED_ORANGE, "w": 34, "h": 28, "speed_mult": 1.0},
    {"color": arcade.color.MAGENTA, "w": 28, "h": 44, "speed_mult": 1.15},
    {"color": arcade.color.ORANGE, "w": 36, "h": 20, "speed_mult": 1.3},
]

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.camera = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()
        self.background_color = arcade.color.BLACK
        self.time = 0

    def setup(self):
        self.player_lane = NUM_LANES // 2
        self.target_lane = self.player_lane
        self.player_x = LANES[self.player_lane]
        self.player_speed_x = 0

        self.score = 0
        self.best_score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.scroll = 0.0
        self.dash_timer = 0.0
        self.speed = 360.0
        self.camera_y = 0.0
        self.shake_time = 0.0
        self.shake_power = 0.0

        self.player = arcade.SpriteSolidColor(PLAYER_SIZE, PLAYER_SIZE, arcade.color.CYAN)
        self.player.center_x = self.player_x
        self.player.center_y = PLAYER_Y

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        self.obstacles = arcade.SpriteList()

        self.star_field = []
        for _ in range(80):
            self.star_field.append(
                [random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)]
            )

    def spawn_obstacle(self):
        t = random.choice(OBSTACLE_TYPES)
        obstacle = arcade.SpriteSolidColor(t["w"], t["h"], t["color"])
        obstacle.center_x = random.choice(LANES)
        obstacle.center_y = HEIGHT + 60
        obstacle.change_y = -self.speed * t["speed_mult"]
        self.obstacles.append(obstacle)

    def draw_background(self):
        arcade.draw_rectangle_filled(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT, arcade.color.BLACK)
        arcade.draw_rectangle_filled(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT, (8, 8, 18))

        for x, y, s in self.star_field:
            arcade.draw_circle_filled(x, y, s, arcade.color.WHITE)

        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            pulse = 90 + int(60 * math.sin(self.time * 3 + i * 0.4))
            arcade.draw_line(x, 0, x, HEIGHT, (pulse, pulse, pulse), 1)

        for y in range(-120, HEIGHT + 120, 120):
            yy = y + (self.scroll % 120)
            arcade.draw_rectangle_filled(WIDTH / 2, yy, WIDTH, 8, (20, 20, 26))

    def on_draw(self):
        self.clear()

        self.camera.use()
        self.draw_background()
        self.obstacles.draw()
        self.player_list.draw()

        self.camera_gui.use()
        arcade.draw_rectangle_filled(WIDTH / 2, HEIGHT - 36, WIDTH, 72, (0, 0, 0, 180))
        arcade.draw_text(f"SCORE {self.score}", 16, HEIGHT - 34, arcade.color.WHITE, 16)
        arcade.draw_text(f"BEST {self.best_score}", 16, HEIGHT - 58, arcade.color.LIGHT_GRAY, 12)
        arcade.draw_text(f"SPEED {int(self.speed)}", WIDTH - 110, HEIGHT - 34, arcade.color.WHITE, 16)

        if self.game_over:
            arcade.draw_rectangle_filled(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT, (0, 0, 0, 140))
            arcade.draw_text("GAME OVER", WIDTH / 2, HEIGHT / 2 + 30, arcade.color.YELLOW, 28, anchor_x="center")
            arcade.draw_text("Press R to Restart", WIDTH / 2, HEIGHT / 2 - 10, arcade.color.WHITE, 16, anchor_x="center")

    def on_update(self, delta_time):
        self.time += delta_time

        if self.game_over:
            self.shake_time = max(0, self.shake_time - delta_time)
            return

        self.score += int(delta_time * 60)
        self.speed = min(900, self.speed + delta_time * 18)
        self.scroll += self.speed * delta_time * 0.35

        self.spawn_timer += delta_time
        spawn_rate = max(0.18, 0.75 - self.score / 2500)

        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0
            for _ in range(random.randint(1, 4)):
                self.spawn_obstacle()

        move_speed = 12
        self.player.center_x += (self.target_lane_x() - self.player.center_x) * min(1, move_speed * delta_time)

        for obstacle in self.obstacles:
            obstacle.center_y += obstacle.change_y * delta_time

        for obstacle in self.obstacles[:]:
            if obstacle.top < -40:
                obstacle.remove_from_sprite_lists()

        if arcade.check_for_collision_with_list(self.player, self.obstacles):
            self.game_over = True
            self.best_score = max(self.best_score, self.score)
            self.shake_time = 0.25
            self.shake_power = 10

        if self.shake_time > 0:
            self.camera.position = (
                random.uniform(-self.shake_power, self.shake_power),
                random.uniform(-self.shake_power, self.shake_power),
            )
        else:
            self.camera.position = (0, 0)

    def target_lane_x(self):
        return LANES[self.target_lane]

    def on_key_press(self, key, modifiers):
        if key in [arcade.key.LEFT, arcade.key.A]:
            self.target_lane = max(0, self.target_lane - 1)
        elif key in [arcade.key.RIGHT, arcade.key.D]:
            self.target_lane = min(NUM_LANES - 1, self.target_lane + 1)
        elif key == arcade.key.R and self.game_over:
            self.setup()

def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    view = GameView()
    view.setup()
    window.show_view(view)
    arcade.run()

if __name__ == "__main__":
    main()
