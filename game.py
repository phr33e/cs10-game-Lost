import arcade
import random

# Screen configuration
NUM_LANES = 100
LANE_WIDTH = 10
WIDTH = NUM_LANES * LANE_WIDTH  # 1000 pixels wide
HEIGHT = 600

# Speed settings
SLIDE_SPEED = 0.8
FORWARD_SPEED = 3.5

# Spacing & Current settings
SPAWN_RATE = 90
CURRENT_HEIGHT = 32000

# Generate coordinates for the center of all 100 lanes
LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

class SimpleRunner100(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "100-Lane Currents MVP")
        arcade.set_background_color(arcade.color.BLACK)
        self.keys_held = set()
        self.reset()

    def reset(self):
        self.player_lane = NUM_LANES // 2
        self.player_x = LANES[self.player_lane]
        self.player_target_x = LANES[self.player_lane]
        self.obstacles = []
        self.currents = []
        self.in_current = False
        self.current_active_speed = FORWARD_SPEED
        self.spawn_timer = 0
        self.score = 0
        self.keys_held.clear()

        # --- Survival Mechanics ---
        self.energy = 100.0                 # Max 100, depletes over 180 seconds
        self.max_food_percentage = 100.0    # Drops by 35% on hit
        self.food_percentage = 100.0        # Current food supply
        self.energy_buffer = 0.0            # Holds energy waiting to be applied
        self.healing_rate = 20.0            # Heals 100 energy over 5 seconds
        self.invulnerable_timer = 0.0
        self.game_over = False

        # --- Day / Night Cycle ---
        self.day_timer = 0.0                # Tracks total game time
        self.day_length = 240.0             # 120s (2 min) day->night, 120s night->day

    def on_draw(self):
        self.clear()

        # 0. Draw faint lanes
        for x in LANES:
            arcade.draw_line(x, 0, x, HEIGHT, (25, 25, 25, 60), 1)

        # 1. Draw Currents
        for curr in self.currents:
            width = curr['size'] * LANE_WIDTH
            center_x = (curr['start_lane'] * LANE_WIDTH) + (width / 2)
            arcade.draw_rect_filled(
                arcade.XYWH(center_x, curr['y'], width, curr['height']),
                (46, 204, 113, 80)
            )

        # 2. Draw Player
        if self.invulnerable_timer <= 0 or int(self.invulnerable_timer * 15) % 2 == 0:
            player_color = arcade.color.LIME_GREEN if self.in_current else arcade.color.CYAN
            arcade.draw_rect_filled(
                arcade.XYWH(self.player_x, 80, LANE_WIDTH - 2, LANE_WIDTH - 2),
                player_color
            )

        # 3. Draw Obstacles
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 2, LANE_WIDTH - 2),
                arcade.color.DARK_GRAY
            )

        # 4. Day/Night Cycle (FOV Reducer)
        # Calculate where we are in the cycle (0.0 is Day, 1.0 is Peak Night)
        cycle_progress = (self.day_timer % self.day_length) / (self.day_length / 2)
        night_intensity = cycle_progress if cycle_progress <= 1.0 else 2.0 - cycle_progress

        if night_intensity > 0.01 and not self.game_over:
            # 1000 radius covers the screen. At peak night, drops down to exactly 10.
            current_fov = 1000.0 - (990.0 * night_intensity)
            alpha = int(255 * night_intensity)

            # Draw a massive shape with a hole in the middle for the FOV
            border_thickness = 4000
            arcade.draw_circle_outline(
                self.player_x, 80,
                radius=current_fov + (border_thickness / 2),
                color=(0, 0, 0, alpha),
                border_width=border_thickness
            )

        # 5. Low Energy Vignette Effect (Stacks under the FOV)
        if self.energy < 30 and not self.game_over:
            darkness = 1.0 - (max(self.energy, 0) / 30.0)
            alpha = int(245 * darkness)
            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
                (0, 0, 0, alpha)
            )

        # 6. Draw UI
        arcade.draw_text(f"SCORE: {int(self.score)}", 15, HEIGHT - 35, arcade.color.WHITE, 16)

        arcade.draw_text(f"FOOD: {self.food_percentage:.1f}% / {self.max_food_percentage:.1f}%",
                         15, HEIGHT - 60, arcade.color.ORANGE, 16, bold=True)
        arcade.draw_text("Press SPACE to eat", 15, HEIGHT - 80, arcade.color.GRAY, 12)

        # Show if we are currently digesting food into energy
        if self.energy_buffer > 0:
            arcade.draw_text("REPLENISHING...", 15, HEIGHT - 100, arcade.color.YELLOW, 12, bold=True)

        if self.in_current:
            multiplier = self.current_active_speed / FORWARD_SPEED
            arcade.draw_text(f"IN CURRENT! x{multiplier:.1f} SPD", WIDTH - 15, HEIGHT - 35,
                             arcade.color.LIME_GREEN, 16, anchor_x="right", bold=True)

        if self.game_over:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), arcade.color.BLACK)
            arcade.draw_text("ENERGY DEPLETED - GAME OVER", WIDTH / 2, HEIGHT / 2, arcade.color.RED, 30, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to Restart", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")

    def on_update(self, delta_time):
        if self.game_over:
            return

        self.spawn_timer += 1
        self.day_timer += delta_time

        # --- Energy Buffer Healing (Over time) ---
        if self.energy_buffer > 0:
            heal_step = self.healing_rate * delta_time
            if heal_step > self.energy_buffer:
                heal_step = self.energy_buffer # Don't over-heal past what's in the buffer

            self.energy_buffer -= heal_step
            self.energy += heal_step

            # Cap energy at 100 and wipe remainder
            if self.energy > 100.0:
                self.energy = 100.0
                self.energy_buffer = 0.0

        # --- Base Energy Depletion (100 energy over 180 seconds) ---
        self.energy -= (100.0 / 180.0) * delta_time
        if self.energy <= 0:
            self.game_over = True

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= delta_time

        # --- Check Currents & Determine Target Speed ---
        self.in_current = False
        target_speed = FORWARD_SPEED

        for curr in self.currents:
            zone_left = curr['start_lane'] * LANE_WIDTH
            zone_right = (curr['start_lane'] + curr['size']) * LANE_WIDTH
            zone_bottom = curr['y'] - curr['height'] / 2
            zone_top = curr['y'] + curr['height'] / 2

            if zone_left <= self.player_x <= zone_right and zone_bottom <= 80 <= zone_top:
                self.in_current = True
                target_speed = curr['speed']
                break

        # --- Fade Speed In/Out smoothly ---
        if self.current_active_speed < target_speed:
            self.current_active_speed += 0.15
            if self.current_active_speed > target_speed:
                self.current_active_speed = target_speed
        elif self.current_active_speed > target_speed:
            self.current_active_speed -= 0.15
            if self.current_active_speed < target_speed:
                self.current_active_speed = target_speed

        # Adjust score gain
        self.score += (self.current_active_speed / FORWARD_SPEED)

        # Move player sideways smoothly
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

        # --- Spawn Loop ---
        if self.spawn_timer >= SPAWN_RATE:
            if len(self.currents) == 0 and random.random() < 0.40:
                roll = random.random()
                if roll < 0.30: size = random.randint(1, 3)
                elif roll < 0.70: size = random.randint(4, 7)
                else: size = random.randint(8, 10)

                current_speed = 13.4 - (size * 0.4)
                start_lane = random.randint(0, NUM_LANES - size)
                self.currents.append({
                    'start_lane': start_lane,
                    'size': size,
                    'speed': current_speed,
                    'y': HEIGHT + (CURRENT_HEIGHT / 2),
                    'height': CURRENT_HEIGHT
                })

            num_clumps = random.randint(2, 5)
            for _ in range(num_clumps):
                center_lane = random.randint(10, NUM_LANES - 11)
                center_y = HEIGHT + random.randint(20, 100)
                clump_size = random.randint(5, 12)

                for _ in range(clump_size):
                    lane_offset = random.randint(-4, 4)
                    y_offset = random.randint(-40, 40)

                    lane_idx = center_lane + lane_offset
                    if 0 <= lane_idx < NUM_LANES:
                        self.obstacles.append([LANES[lane_idx], center_y + y_offset])

            self.spawn_timer = 0

        # Move currents
        for curr in self.currents[:]:
            curr['y'] -= self.current_active_speed
            if curr['y'] + (curr['height'] / 2) < 0:
                self.currents.remove(curr)

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= self.current_active_speed

            # --- Collision detection ---
            if self.invulnerable_timer <= 0:
                if abs(self.player_x - obs[0]) < 8 and abs(obs[1] - 80) < 14:
                    self.energy -= 70.0

                    self.max_food_percentage *= 0.65
                    if self.food_percentage > self.max_food_percentage:
                        self.food_percentage = self.max_food_percentage

                    self.invulnerable_timer = 1.0
                    self.obstacles.remove(obs)
                    continue

            # Remove off-screen obstacles
            if obs[1] < -20:
                self.obstacles.remove(obs)

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.ENTER:
                self.reset()
            return

        if key in [arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D]:
            self.keys_held.add(key)

        if self.player_x == self.player_target_x:
            if key in [arcade.key.LEFT, arcade.key.A] and self.player_lane > 0:
                self.player_lane -= 1
                self.player_target_x = LANES[self.player_lane]
            elif key in [arcade.key.RIGHT, arcade.key.D] and self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.player_target_x = LANES[self.player_lane]

        # --- Use Food Mechanic ---
        if key == arcade.key.SPACE:
            if self.food_percentage > 0 and self.energy < 100:
                # Take a random bite size (between 5% and 25%)
                food_to_eat = random.uniform(5.0, 25.0)

                # Make sure we don't eat more than we actually have left
                if food_to_eat > self.food_percentage:
                    food_to_eat = self.food_percentage

                self.food_percentage -= food_to_eat

                # Add it to the buffer to be converted to energy over time
                # 1% food eaten = 1 energy to heal
                self.energy_buffer += food_to_eat

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)


if __name__ == "__main__":
    SimpleRunner100()
    arcade.run()
