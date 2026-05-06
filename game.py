import arcade
import random

# Screen configuration
NUM_LANES = 100
LANE_WIDTH = 10
WIDTH = NUM_LANES * LANE_WIDTH  # 1000 pixels wide
HEIGHT = 600

# Speed settings
SLIDE_SPEED = 0.8      # Slow, steady sideways movement stays the same
FORWARD_SPEED = 3.5    # Normal forward speed

# Spacing & Current settings
SPAWN_RATE = 90
CURRENT_HEIGHT = 32000  # Long-lasting runway (at least 60 seconds)

# Generate coordinates for the center of all 100 lanes
LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

class SimpleRunner100(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "100-Lane Currents MVP")
        arcade.set_background_color(arcade.color.BLACK)
        self.keys_held = set()  # Track which keys are currently pressed
        self.reset()

    def reset(self):
        self.player_lane = NUM_LANES // 2  # Start in the middle
        self.player_x = LANES[self.player_lane]
        self.player_target_x = LANES[self.player_lane]
        self.obstacles = []  # Stores [x, y] coordinates
        self.currents = []  # Stores active currents
        self.in_current = False
        self.current_active_speed = FORWARD_SPEED
        self.spawn_timer = 0
        self.score = 0
        self.keys_held.clear()  # Clear held keys on reset

    def on_draw(self):
        self.clear()

        # 1. Draw Currents (drawn first so they sit behind player/obstacles)
        for curr in self.currents:
            width = curr['size'] * LANE_WIDTH
            center_x = (curr['start_lane'] * LANE_WIDTH) + (width / 2)
            # Draw semi-transparent glowing green runway
            arcade.draw_rect_filled(
                arcade.XYWH(center_x, curr['y'], width, curr['height']),
                (46, 204, 113, 80)  # Green with transparency
            )

        # 2. Draw Player (Cyan normally, Neon Green when in a current)
        player_color = arcade.color.LIME_GREEN if self.in_current else arcade.color.CYAN
        arcade.draw_rect_filled(
            arcade.XYWH(self.player_x, 80, LANE_WIDTH - 2, LANE_WIDTH - 2),
            player_color
        )

        # 3. Draw Obstacles (Red rectangles)
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 2, 20),
                arcade.color.RED
            )

        # 4. Draw Score and Current Status
        arcade.draw_text(f"SCORE: {int(self.score)}", 15, HEIGHT - 35, arcade.color.WHITE, 16)

        if self.in_current:
            # Show the multiplier relative to normal forward speed
            multiplier = self.current_active_speed / FORWARD_SPEED
            arcade.draw_text(f"IN CURRENT! x{multiplier:.1f} SPD", WIDTH - 15, HEIGHT - 35,
                             arcade.color.LIME_GREEN, 16, anchor_x="right", bold=True)

    def on_update(self, delta_time):
        self.spawn_timer += 1

        # Check if the player is currently inside the active current
        self.in_current = False
        self.current_active_speed = FORWARD_SPEED

        for curr in self.currents:
            zone_left = curr['start_lane'] * LANE_WIDTH
            zone_right = (curr['start_lane'] + curr['size']) * LANE_WIDTH
            zone_bottom = curr['y'] - curr['height'] / 2
            zone_top = curr['y'] + curr['height'] / 2

            # If player is within the boundaries of this current
            if zone_left <= self.player_x <= zone_right and zone_bottom <= 80 <= zone_top:
                self.in_current = True
                self.current_active_speed = curr['speed']
                break

        # Adjust score gain based on how fast you are moving
        self.score += (self.current_active_speed / FORWARD_SPEED)

        # Move player_x towards player_target_x steadily (SLIDE_SPEED remains constant)
        if self.player_x < self.player_target_x:
            self.player_x = min(self.player_target_x, self.player_x + SLIDE_SPEED)
        elif self.player_x > self.player_target_x:
            self.player_x = max(self.player_target_x, self.player_x - SLIDE_SPEED)

        # Continuous movement check for holding keys
        if self.player_x == self.player_target_x:
            if (arcade.key.LEFT in self.keys_held or arcade.key.A in self.keys_held) and self.player_lane > 0:
                self.player_lane -= 1
                self.player_target_x = LANES[self.player_lane]
            elif (arcade.key.RIGHT in self.keys_held or arcade.key.D in self.keys_held) and self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.player_target_x = LANES[self.player_lane]

        # Spawn loop
        if self.spawn_timer >= SPAWN_RATE:
            # Try to spawn a new current if none exist
            if len(self.currents) == 0 and random.random() < 0.40:
                # 1. Determine size using probability brackets
                roll = random.random()
                if roll < 0.10:    # 10% chance
                    size = random.randint(1, 5)
                elif roll < 0.60:  # 50% chance (0.10 to 0.60)
                    size = random.randint(6, 10)
                else:              # 40% chance (0.60 to 1.00)
                    size = random.randint(11, 20)

                # 2. Determine speed based on size (the smaller the current, the faster the speed)
                # Max speed is ~13.0 for size 1, Min speed is ~5.4 for size 20
                current_speed = 13.4 - (size * 0.4)

                start_lane = random.randint(0, NUM_LANES - size)
                self.currents.append({
                    'start_lane': start_lane,
                    'size': size,
                    'speed': current_speed,
                    'y': HEIGHT + (CURRENT_HEIGHT / 2),
                    'height': CURRENT_HEIGHT
                })

            # Spawn obstacle clumps
            num_clumps = random.randint(2, 4)
            for _ in range(num_clumps):
                clump_center = random.randint(5, NUM_LANES - 6)
                clump_size = random.randint(3, 10)
                for offset in range(-clump_size // 2, (clump_size // 2) + 1):
                    lane_idx = clump_center + offset
                    if 0 <= lane_idx < NUM_LANES:
                        self.obstacles.append([LANES[lane_idx], HEIGHT + 20])

            self.spawn_timer = 0

        # Move and clean up currents
        for curr in self.currents[:]:
            curr['y'] -= self.current_active_speed
            if curr['y'] + (curr['height'] / 2) < 0:
                self.currents.remove(curr)

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= self.current_active_speed

            # Collision detection
            if abs(self.player_x - obs[0]) < 8 and abs(obs[1] - 80) < 14:
                self.reset()  # Instant restart on hit

            # Remove off-screen obstacles
            if obs[1] < -20:
                self.obstacles.remove(obs)

    def on_key_press(self, key, modifiers):
        # Add key to the active held keys set
        if key in [arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D]:
            self.keys_held.add(key)

        # Instant tap responsiveness
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
    SimpleRunner100()
    arcade.run()
