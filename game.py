import arcade
import random

# Screen configuration
NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH  # 800 pixels wide
HEIGHT = 600

# SLIDE_SPEED controls how fast the player moves between lanes.
# Try 0.05 for very slow, 0.1 for medium, or 0.2 for fast.
SLIDE_SPEED = 0.10

# Generate coordinates for the center of all 20 lanes
LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

class SimpleRunner20(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "20-Lane Subway Surfers MVP")
        arcade.set_background_color(arcade.color.BLACK)
        self.reset()

    def reset(self):
        self.player_lane = NUM_LANES // 2  # Start in the middle lane
        self.player_x = LANES[self.player_lane]  # Current actual X position
        self.player_target_x = LANES[self.player_lane]  # Destination X position
        self.obstacles = []  # Stores [x, y] coordinates
        self.spawn_timer = 0
        self.score = 0

    def on_draw(self):
        self.clear()

        # Draw 19 lane divider lines
        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            arcade.draw_line(x, 0, x, HEIGHT, arcade.color.DARK_GRAY, 1)

        # Draw Player (Cyan square, using self.player_x for smooth rendering)
        arcade.draw_rect_filled(
            arcade.XYWH(self.player_x, 80, LANE_WIDTH - 10, LANE_WIDTH - 10),
            arcade.color.CYAN
        )

        # Draw Obstacles (Red rectangles)
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 6, 30),
                arcade.color.RED
            )

        # Draw Score
        arcade.draw_text(f"SCORE: {self.score}", 15, HEIGHT - 35, arcade.color.WHITE, 16)

    def on_update(self, delta_time):
        self.score += 1
        self.spawn_timer += 1

        # Smoothly slide the player toward the target lane
        dx = self.player_target_x - self.player_x
        self.player_x += dx * SLIDE_SPEED

        # Spawn obstacles in groups to fill 20 lanes
        if self.spawn_timer >= 12:
            for _ in range(random.randint(1, 4)):
                self.obstacles.append([random.choice(LANES), HEIGHT + 20])
            self.spawn_timer = 0

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= 7  # Obstacle speed

            # Collision: check distance between player's actual X and obstacle X
            # This ensures collision works perfectly even while the player is mid-slide!
            if abs(self.player_x - obs[0]) < (LANE_WIDTH - 8) and abs(obs[1] - 80) < 35:
                self.reset()  # Instant restart on hit

            # Remove off-screen obstacles
            if obs[1] < -20:
                self.obstacles.remove(obs)

    def on_key_press(self, key, modifiers):
        # Update target lane and target X destination
        if key in [arcade.key.LEFT, arcade.key.A] and self.player_lane > 0:
            self.player_lane -= 1
            self.player_target_x = LANES[self.player_lane]
        elif key in [arcade.key.RIGHT, arcade.key.D] and self.player_lane < NUM_LANES - 1:
            self.player_lane += 1
            self.player_target_x = LANES[self.player_lane]

if __name__ == "__main__":
    SimpleRunner20()
    arcade.run()
