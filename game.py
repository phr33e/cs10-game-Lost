import arcade
import random

# Screen configuration
WIDTH, HEIGHT = 400, 600
LANE_WIDTH = WIDTH // 3
LANES = [LANE_WIDTH // 2, LANE_WIDTH + LANE_WIDTH // 2, LANE_WIDTH * 2 + LANE_WIDTH // 2]

class SimpleRunner(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Subway Surfers MVP")
        arcade.set_background_color(arcade.color.BLACK)
        self.reset()

    def reset(self):
        self.player_lane = 1
        self.obstacles = []  # Stores [x, y] coordinates
        self.spawn_timer = 0
        self.score = 0

    def on_draw(self):
        self.clear()

        # Draw 3 Lanes
        arcade.draw_line(LANE_WIDTH, 0, LANE_WIDTH, HEIGHT, arcade.color.GRAY, 2)
        arcade.draw_line(LANE_WIDTH * 2, 0, LANE_WIDTH * 2, HEIGHT, arcade.color.GRAY, 2)

        # Draw Player (Cyan square)
        arcade.draw_rect_filled(
            arcade.XYWH(LANES[self.player_lane], 80, 40, 40),
            arcade.color.CYAN
        )

        # Draw Obstacles (Red rectangles)
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], 60, 40),
                arcade.color.RED
            )

        # Draw Score
        arcade.draw_text(f"SCORE: {self.score}", 15, HEIGHT - 35, arcade.color.WHITE, 16)

    def on_update(self, delta_time):
        self.score += 1
        self.spawn_timer += 1

        # Spawn a new obstacle at the top every 45 frames
        if self.spawn_timer >= 45:
            self.obstacles.append([random.choice(LANES), HEIGHT + 20])
            self.spawn_timer = 0

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= 7  # Obstacle speed

            # Simple collision: if obstacle is in the player's lane and hits player's height
            if obs[0] == LANES[self.player_lane] and abs(obs[1] - 80) < 40:
                self.reset()  # Crash! Instantly restart the game.

            # Remove off-screen obstacles
            if obs[1] < -20:
                self.obstacles.remove(obs)

    def on_key_press(self, key, modifiers):
        # Instant lane snapping
        if key in [arcade.key.LEFT, arcade.key.A] and self.player_lane > 0:
            self.player_lane -= 1
        elif key in [arcade.key.RIGHT, arcade.key.D] and self.player_lane < 2:
            self.player_lane += 1

if __name__ == "__main__":
    SimpleRunner()
    arcade.run()
