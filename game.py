import arcade
import random

# Screen configuration
NUM_LANES = 40
LANE_WIDTH = 20
WIDTH = NUM_LANES * LANE_WIDTH  # 800 pixels wide
HEIGHT = 600

# Speed settings
SLIDE_SPEED = 1.5      # Turning speed stays exactly the same
FORWARD_SPEED = 3.5    # Normal forward speed
BOOST_SPEED = 8.5      # Faster forward speed when in the 8-lane boost zone

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
        self.boost_zones = []  # Stores boost zones: {'start_lane': int, 'y': float, 'height': int}
        self.is_boosting = False
        self.spawn_timer = 0
        self.score = 0
        self.keys_held.clear()  # Clear held keys on reset

    def on_draw(self):
        self.clear()

        # 1. Draw Boost Zones (drawn first so they sit behind player and obstacles)
        for bz in self.boost_zones:
            width = 8 * LANE_WIDTH
            center_x = (bz['start_lane'] * LANE_WIDTH) + (width / 2)
            # Draw semi-transparent glowing green runway
            arcade.draw_rect_filled(
                arcade.XYWH(center_x, bz['y'], width, bz['height']),
                (46, 204, 113, 80)  # Green with transparency
            )

        # 2. Draw Player (Cyan normally, Neon Green when boosting)
        player_color = arcade.color.LIME_GREEN if self.is_boosting else arcade.color.CYAN
        arcade.draw_rect_filled(
            arcade.XYWH(self.player_x, 80, LANE_WIDTH - 4, LANE_WIDTH - 4),
            player_color
        )

        # 3. Draw Obstacles (Red rectangles)
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 4, 30),
                arcade.color.RED
            )

        # 4. Draw Score and Boost Indicator
        arcade.draw_text(f"SCORE: {int(self.score)}", 15, HEIGHT - 35, arcade.color.WHITE, 16)

        if self.is_boosting:
            arcade.draw_text("BOOSTING! x2.5 SPD", WIDTH - 15, HEIGHT - 35,
                             arcade.color.LIME_GREEN, 16, anchor_x="right", bold=True)

    def on_update(self, delta_time):
        self.spawn_timer += 1

        # Check if the player is currently inside any of the active 8-lane boost zones
        self.is_boosting = False
        for bz in self.boost_zones:
            zone_left = bz['start_lane'] * LANE_WIDTH
            zone_right = (bz['start_lane'] + 8) * LANE_WIDTH
            zone_bottom = bz['y'] - bz['height'] / 2
            zone_top = bz['y'] + bz['height'] / 2

            # If player's X is within the 8 lanes, and player's Y (80) is vertically on the pad
            if zone_left <= self.player_x <= zone_right and zone_bottom <= 80 <= zone_top:
                self.is_boosting = True
                break

        # Adjust game dynamics based on boost state
        current_forward_speed = BOOST_SPEED if self.is_boosting else FORWARD_SPEED
        self.score += 2.5 if self.is_boosting else 1.0

        # Move player_x towards player_target_x slowly and steadily (SLIDE_SPEED remains constant)
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

        # Spawn loop
        if self.spawn_timer >= SPAWN_RATE:
            # 35% chance to spawn an 8-lane wide boost runway
            if random.random() < 0.35:
                start_lane = random.randint(0, NUM_LANES - 8)
                self.boost_zones.append({
                    'start_lane': start_lane,
                    'y': HEIGHT + 150,
                    'height': 300
                })

            # Spawn obstacle clumps
            num_clumps = random.choice([1, 2])
            for _ in range(num_clumps):
                clump_center = random.randint(3, NUM_LANES - 4)
                clump_size = random.randint(3, 7)
                for offset in range(-clump_size // 2, (clump_size // 2) + 1):
                    lane_idx = clump_center + offset
                    if 0 <= lane_idx < NUM_LANES:
                        self.obstacles.append([LANES[lane_idx], HEIGHT + 20])
            self.spawn_timer = 0

        # Move and clean up boost zones
        for bz in self.boost_zones[:]:
            bz['y'] -= current_forward_speed
            if bz['y'] < -200:
                self.boost_zones.remove(bz)

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= current_forward_speed

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
