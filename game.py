import arcade
import random

# Screen configuration
NUM_LANES = 40
LANE_WIDTH = 20
WIDTH = NUM_LANES * LANE_WIDTH  # 800 pixels wide
HEIGHT = 600

# Speed settings
SLIDE_SPEED = 5.0      # Constant speed (pixels per frame) for perfectly fluid sweeping
FORWARD_SPEED = 3.5

# Obstacle Spacing Settings
SPAWN_RATE = 90

# Generate coordinates for the center of all 40 lanes
LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

class SimpleRunner40(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "40-Lane Subway Surfers MVP")
        arcade.set_background_color(arcade.color.BLACK)
        self.keys_held = set()  # Track which keys are currently pressed
        self.reset()

    def reset(self):
        self.player_lane = NUM_LANES // 2  # Start in the middle lane
        self.player_x = LANES[self.player_lane]
        self.player_target_x = LANES[self.player_lane]
        self.obstacles = []  # Stores [x, y] coordinates
        self.spawn_timer = 0
        self.score = 0
        self.keys_held.clear()  # Clear held keys on reset

    def on_draw(self):
        self.clear()

        # Draw Player (Cyan square)
        arcade.draw_rect_filled(
            arcade.XYWH(self.player_x, 80, LANE_WIDTH - 4, LANE_WIDTH - 4),
            arcade.color.CYAN
        )

        # Draw Obstacles (Red rectangles)
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 4, 30),
                arcade.color.RED
            )

        # Draw Score
        arcade.draw_text(f"SCORE: {self.score}", 15, HEIGHT - 35, arcade.color.WHITE, 16)

    def on_update(self, delta_time):
        self.score += 1
        self.spawn_timer += 1

        # Move player_x towards player_target_x at a constant velocity
        if self.player_x < self.player_target_x:
            self.player_x = min(self.player_target_x, self.player_x + SLIDE_SPEED)
        elif self.player_x > self.player_target_x:
            self.player_x = max(self.player_target_x, self.player_x - SLIDE_SPEED)

        # Continuous movement check: If we have fully arrived at our current target lane,
        # immediately set the next lane target without stopping or pausing.
        if self.player_x == self.player_target_x:
            if (arcade.key.LEFT in self.keys_held or arcade.key.A in self.keys_held) and self.player_lane > 0:
                self.player_lane -= 1
                self.player_target_x = LANES[self.player_lane]
            elif (arcade.key.RIGHT in self.keys_held or arcade.key.D in self.keys_held) and self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.player_target_x = LANES[self.player_lane]

        # Spawn obstacles in tight horizontal clumps
        if self.spawn_timer >= SPAWN_RATE:
            num_clumps = random.choice([1, 2])
            for _ in range(num_clumps):
                clump_center = random.randint(3, NUM_LANES - 4)
                clump_size = random.randint(3, 7)
                for offset in range(-clump_size // 2, (clump_size // 2) + 1):
                    lane_idx = clump_center + offset
                    if 0 <= lane_idx < NUM_LANES:
                        self.obstacles.append([LANES[lane_idx], HEIGHT + 20])
            self.spawn_timer = 0

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= FORWARD_SPEED

            # Collision detection
            if abs(self.player_x - obs[0]) < (LANE_WIDTH - 4) and abs(obs[1] - 80) < 23:
                self.reset()  # Instant restart on hit

            # Remove off-screen obstacles
            if obs[1] < -20:
                self.obstacles.remove(obs)

    def on_key_press(self, key, modifiers):
        # Add key to the active held keys set
        if key in [arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D]:
            self.keys_held.add(key)

        # Instant tap responsiveness (moves immediately on initial press if stationary)
        if self.player_x == self.player_target_x:
            if key in [arcade.key.LEFT, arcade.key.A] and self.player_lane > 0:
                self.player_lane -= 1
                self.player_target_x = LANES[self.player_lane]
            elif key in [arcade.key.RIGHT, arcade.key.D] and self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.player_target_x = LANES[self.player_lane]

    def on_key_release(self, key, modifiers):
        # Remove key from the active held keys set
        self.keys_held.discard(key)

if __name__ == "__main__":
    SimpleRunner40()
    arcade.run()
