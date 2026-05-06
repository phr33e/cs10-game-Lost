import arcade
import random

NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 600
TITLE = "20-Lane Subway Surfers MVP"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]
PLAYER_Y = 80
OBSTACLE_START_Y = HEIGHT + 30
OBSTACLE_SPEED_START = 280
OBSTACLE_SPEED_MAX = 650


class SimpleRunner20(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        arcade.set_background_color(arcade.color.BLACK)
        self.setup()

    def setup(self):
        self.player_lane = NUM_LANES // 2
        self.score = 0
        self.distance = 0
        self.game_over = False
        self.obstacle_speed = OBSTACLE_SPEED_START
        self.spawn_timer = 0.0

        self.player_sprite = arcade.SpriteSolidColor(
            LANE_WIDTH - 10, LANE_WIDTH - 10, arcade.color.CYAN
        )
        self.player_sprite.center_x = LANES[self.player_lane]
        self.player_sprite.center_y = PLAYER_Y

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player_sprite)

        self.obstacle_list = arcade.SpriteList()
        self.line_list = arcade.SpriteList()

        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            line = arcade.SpriteSolidColor(2, HEIGHT, arcade.color.DARK_GRAY)
            line.center_x = x
            line.center_y = HEIGHT / 2
            self.line_list.append(line)

    def spawn_obstacle(self):
        obstacle = arcade.SpriteSolidColor(LANE_WIDTH - 6, 30, arcade.color.RED)
        obstacle.center_x = random.choice(LANES)
        obstacle.center_y = OBSTACLE_START_Y
        self.obstacle_list.append(obstacle)

    def on_draw(self):
        self.clear()
        self.line_list.draw()
        self.obstacle_list.draw()
        self.player_list.draw()

        arcade.draw_text(
            f"SCORE: {self.score}",
            15,
            HEIGHT - 35,
            arcade.color.WHITE,
            16,
        )

        if self.game_over:
            arcade.draw_text(
                "GAME OVER - Press R to Restart",
                WIDTH / 2,
                HEIGHT / 2,
                arcade.color.YELLOW,
                18,
                anchor_x="center",
            )

    def on_update(self, delta_time):
        if self.game_over:
            return

        self.distance += delta_time
        self.score = int(self.distance * 10)
        self.obstacle_speed = min(
            OBSTACLE_SPEED_MAX, OBSTACLE_SPEED_START + self.distance * 15
        )

        self.spawn_timer += delta_time
        spawn_interval = max(0.25, 0.9 - self.distance * 0.01)

        if self.spawn_timer >= spawn_interval:
            self.spawn_timer = 0
            for _ in range(random.randint(1, 3)):
                self.spawn_obstacle()

        for obstacle in self.obstacle_list:
            obstacle.center_y -= self.obstacle_speed * delta_time

        if arcade.check_for_collision_with_list(self.player_sprite, self.obstacle_list):
            self.game_over = True

        for obstacle in self.obstacle_list[:]:
            if obstacle.top < 0:
                obstacle.remove_from_sprite_lists()

    def on_key_press(self, key, modifiers):
        if key in [arcade.key.LEFT, arcade.key.A] and self.player_lane > 0:
            self.player_lane -= 1
            self.player_sprite.center_x = LANES[self.player_lane]

        elif key in [arcade.key.RIGHT, arcade.key.D] and self.player_lane < NUM_LANES - 1:
            self.player_lane += 1
            self.player_sprite.center_x = LANES[self.player_lane]

        elif key == arcade.key.R and self.game_over:
            self.setup()


if __name__ == "__main__":
    SimpleRunner20()
    arcade.run()
