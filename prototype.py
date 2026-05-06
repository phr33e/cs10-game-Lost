import arcade
import random

# --- Screen configuration ---
NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 600
TITLE = "20-Lane Runner – Playable Version"

# Precompute x positions for lane centers
LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

PLAYER_Y = 80
PLAYER_SIZE = LANE_WIDTH - 10
OBSTACLE_WIDTH = LANE_WIDTH - 6
OBSTACLE_HEIGHT = 30


class RunnerGame(arcade.Window):
    """Simple, fully playable 20-lane runner."""

    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        self.player_lane = NUM_LANES // 2
        self.player_x = LANES[self.player_lane]

        # Obstacles are simple dicts: {"x": ..., "y": ...}
        self.obstacles = []

        self.score = 0
        self.game_over = False

        # Timers / difficulty
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

    def reset(self):
        """Reset game state for a new run."""
        self.player_lane = NUM_LANES // 2
        self.player_x = LANES[self.player_lane]
        self.obstacles = []
        self.score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

    # --- DRAWING ---

    def on_draw(self):
        self.clear()

        # Lane divider lines
        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            arcade.draw_line(
                x, 0, x, HEIGHT,
                arcade.color.DARK_GRAY, 1
            )

        # Player (cyan rectangle)
        arcade.draw_rectangle_filled(
            self.player_x,
            PLAYER_Y,
            PLAYER_SIZE,
            PLAYER_SIZE,
            arcade.color.CYAN
        )

        # Obstacles (red rectangles)
        for obs in self.obstacles:
            arcade.draw_rectangle_filled(
                obs["x"],
                obs["y"],
                OBSTACLE_WIDTH,
                OBSTACLE_HEIGHT,
                arcade.color.RED
            )

        # Score display
        arcade.draw_text(
            f"SCORE: {self.score}",
            15,
            HEIGHT - 35,
            arcade.color.WHITE,
            16,
        )

        if self.game_over:
            arcade.draw_text(
                "GAME OVER – Press R to restart",
                WIDTH / 2,
                HEIGHT / 2 + 10,
                arcade.color.YELLOW,
                18,
                anchor_x="center",
            )

    # --- GAME LOGIC ---

    def on_update(self, delta_time: float):
        if self.game_over:
            return

        self.game_time += delta_time
        self.score += 1

        # Increase speed slowly over time
        self.obstacle_speed = 7.0 + self.game_time * 0.4

        # Spawn obstacles at intervals that shrink as you survive longer
        self.spawn_timer += delta_time
        spawn_interval = max(0.25, 0.9 - self.game_time * 0.04)

        if self.spawn_timer >= spawn_interval:
            self.spawn_timer = 0.0

            # Spawn 1–3 obstacles in random lanes
            lanes_this_wave = random.sample(LANES, k=random.randint(1, 3))
            for lane_x in lanes_this_wave:
                self.obstacles.append({"x": lane_x, "y": HEIGHT + 40})

        # Move obstacles down
        for obs in self.obstacles:
            obs["y"] -= self.obstacle_speed

        # Collision check
        # Player rectangle bounds:
        player_left = self.player_x - PLAYER_SIZE / 2
        player_right = self.player_x + PLAYER_SIZE / 2
        player_bottom = PLAYER_Y - PLAYER_SIZE / 2
        player_top = PLAYER_Y + PLAYER_SIZE / 2

        for obs in self.obstacles:
            obs_left = obs["x"] - OBSTACLE_WIDTH / 2
            obs_right = obs["x"] + OBSTACLE_WIDTH / 2
            obs_bottom = obs["y"] - OBSTACLE_HEIGHT / 2
            obs_top = obs["y"] + OBSTACLE_HEIGHT / 2

            overlap_x = not (obs_right < player_left or obs_left > player_right)
            overlap_y = not (obs_top < player_bottom or obs_bottom > player_top)

            if overlap_x and overlap_y:
                self.game_over = True
                break

        # Remove off-screen obstacles
        self.obstacles = [o for o in self.obstacles if o["y"] > -40]

    # --- INPUT ---

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            if self.player_lane > 0:
                self.player_lane -= 1
                self.player_x = LANES[self.player_lane]

        elif key in (arcade.key.RIGHT, arcade.key.D):
            if self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.player_x = LANES[self.player_lane]

        elif key == arcade.key.R:
            if self.game_over:
                self.reset()


def main():
    game = RunnerGame()
    arcade.run()


if __name__ == "__main__":
    main()
