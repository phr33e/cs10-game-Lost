import arcade
import random

# Screen configuration
NUM_LANES = 150
LANE_WIDTH = 8
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 900

# Player position
PLAYER_Y = HEIGHT // 2

# Speed settings
SLIDE_SPEED = 0.25
FORWARD_SPEED = 1.1

# Spacing & Current settings
SPAWN_RATE = 90
CURRENT_HEIGHT = 32000

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

# --- Custom Pixel Art Boat ---
# M = Metal Grey (Pontoon)
# D = Dark Wood/Brown (Inside the boat / passengers)
BOAT_ART = [
    "  MM  ",
    " MMMM ",
    "MMDDMM",
    "MDDDDM",
    "MDDDDM",
    "MDDDDM",
    "MDDDDM",
    "MDDDDM",
    "MDDDDM",
    "MDDDDM",
    "MDDDDM",
    "MDDDDM",
    "MMDDMM",
    " MMMM "
]

class MediterraneanJourney(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Mediterranean Journey")
        # Fixed: Using a custom RGB color for deep ocean blue
        arcade.set_background_color((15, 35, 75))
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
        self.energy = 100.0
        self.max_food_percentage = 100.0
        self.food_percentage = 100.0
        self.energy_buffer = 0.0
        self.healing_rate = 5.0
        self.invulnerable_timer = 0.0

        # --- Engine Failure Mechanics ---
        self.engine_failure_chance = 0.01
        self.engine_check_timer = 0.0
        self.next_engine_check = random.uniform(300.0, 420.0)
        self.engine_failed = False
        self.engine_repair_timer = 0.0

        self.game_over = False
        self.rescued = False

        # --- Day / Night Cycle ---
        self.day_timer = 0.0
        self.morning_duration = 180.0
        self.night_transition_speed = 1200.0

    def on_draw(self):
        self.clear()

        # 0. Draw faint lanes (Changed to faint white to look like water ripples)
        for x in LANES:
            arcade.draw_line(x, 0, x, HEIGHT, (255, 255, 255, 20), 1)

        # 1. Draw Currents
        for curr in self.currents:
            width = curr['size'] * LANE_WIDTH
            center_x = (curr['start_lane'] * LANE_WIDTH) + (width / 2)
            arcade.draw_rect_filled(
                arcade.XYWH(center_x, curr['y'], width, curr['height']),
                (46, 204, 113, 80)
            )

        # 2. Draw Obstacles (Rocks/Debris)
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 2, LANE_WIDTH - 2),
                arcade.color.DARK_GRAY
            )

        # 3. Day/Night Cycle
        night_intensity = 0.0
        if self.day_timer > self.morning_duration:
            time_in_cycle = (self.day_timer - self.morning_duration) % (self.night_transition_speed * 2)
            if time_in_cycle < self.night_transition_speed:
                night_intensity = time_in_cycle / self.night_transition_speed
            else:
                night_intensity = 2.0 - (time_in_cycle / self.night_transition_speed)

        if night_intensity > 0.01 and not self.game_over and not self.rescued:
            current_fov = 1500.0 - (1300.0 * night_intensity)
            num_bands = 15
            max_radius = 2000
            band_thickness = (max_radius - current_fov) / num_bands

            for i in range(num_bands):
                r = current_fov + (i * band_thickness)
                band_alpha = int((255 * night_intensity) * ((i + 1) / num_bands))
                arcade.draw_circle_outline(
                    self.player_x, PLAYER_Y,
                    radius=r + (band_thickness / 2),
                    color=(0, 0, 0, band_alpha),
                    border_width=band_thickness + 2
                )

        # 4. Low Energy Vignette
        if self.energy < 15 and not self.game_over and not self.rescued:
            darkness = 1.0 - (max(self.energy, 0) / 15.0)
            alpha = int(245 * darkness)
            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
                (0, 0, 0, alpha)
            )

        # 5. Draw Pixelated Player Boat
        if self.invulnerable_timer <= 0 or int(self.invulnerable_timer * 15) % 2 == 0:
            pontoon_color = arcade.color.SLATE_GRAY
            inside_color = arcade.color.BISTRE

            # Status colors override the pontoon
            if self.in_current:
                pontoon_color = arcade.color.LIME_GREEN
            if self.engine_failed:
                pontoon_color = arcade.color.FIREBRICK

            start_x = self.player_x - 3
            start_y = PLAYER_Y + 7

            # Loop through the custom array and draw 1x1 pixels
            for row_idx, row_str in enumerate(BOAT_ART):
                for col_idx, char in enumerate(row_str):
                    if char == 'M':
                        arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), pontoon_color)
                    elif char == 'D':
                        arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), inside_color)

        # 6. Draw UI
        arcade.draw_text(f"FOOD: {self.food_percentage:.1f}% / {self.max_food_percentage:.1f}%",
                         15, HEIGHT - 35, arcade.color.ORANGE, 16, bold=True)
        arcade.draw_text("Press SPACE to eat", 15, HEIGHT - 55, arcade.color.WHITE, 12)

        if self.energy_buffer > 0:
            arcade.draw_text("REPLENISHING...", 15, HEIGHT - 75, arcade.color.YELLOW, 12, bold=True)

        if self.engine_failed:
            arcade.draw_text("ENGINE FAILURE - DRIFTING", 15, HEIGHT - 95, arcade.color.RED, 14, bold=True)

        if self.in_current and not self.engine_failed:
            multiplier = self.current_active_speed / FORWARD_SPEED
            arcade.draw_text(f"IN CURRENT! x{multiplier:.1f} SPD", WIDTH - 15, HEIGHT - 35,
                             arcade.color.LIME_GREEN, 16, anchor_x="right", bold=True)

        # End States
        if self.rescued:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 200))
            arcade.draw_text("LAMPEDUSA COAST SIGHTED. YOU SURVIVED.", WIDTH / 2, HEIGHT / 2, arcade.color.GOLD, 24, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to Restart", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")

        elif self.game_over:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), arcade.color.BLACK)
            arcade.draw_text("THE JOURNEY HAS ENDED", WIDTH / 2, HEIGHT / 2, arcade.color.RED, 30, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to Restart", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")

    def on_update(self, delta_time):
        if self.game_over or self.rescued:
            return

        self.spawn_timer += 1
        self.day_timer += delta_time

        # --- Check Win Condition (Arriving at Lampedusa) ---
        if self.score >= 30000:
            self.rescued = True
            return

        # --- Engine Failure Logic ---
        if self.engine_failed:
            self.engine_repair_timer -= delta_time
            if self.engine_repair_timer <= 0:
                self.engine_failed = False
        else:
            self.engine_check_timer += delta_time
            if self.engine_check_timer >= self.next_engine_check:
                if random.random() < self.engine_failure_chance:
                    self.engine_failed = True
                    self.engine_repair_timer = 60.0

                self.engine_check_timer = 0.0
                self.next_engine_check = random.uniform(300.0, 420.0)

        # --- Energy Buffer Healing ---
        if self.energy_buffer > 0:
            heal_step = self.healing_rate * delta_time
            if heal_step > self.energy_buffer:
                heal_step = self.energy_buffer

            self.energy_buffer -= heal_step
            self.energy += heal_step

            if self.energy > 100.0:
                self.energy = 100.0
                self.energy_buffer = 0.0

        # --- Base Energy Depletion ---
        self.energy -= (1.0 / 60.0) * delta_time
        if self.energy <= 0:
            self.game_over = True

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= delta_time

        # --- Check Currents & Determine Target Speed ---
        self.in_current = False
        target_speed = FORWARD_SPEED

        if self.engine_failed:
            target_speed = FORWARD_SPEED * 0.1
        else:
            for curr in self.currents:
                zone_left = curr['start_lane'] * LANE_WIDTH
                zone_right = (curr['start_lane'] + curr['size']) * LANE_WIDTH
                zone_bottom = curr['y'] - curr['height'] / 2
                zone_top = curr['y'] + curr['height'] / 2

                if zone_left <= self.player_x <= zone_right and zone_bottom <= PLAYER_Y <= zone_top:
                    self.in_current = True
                    target_speed = curr['speed']
                    break

        # --- Fade Speed ---
        if self.current_active_speed < target_speed:
            self.current_active_speed += 0.15
            if self.current_active_speed > target_speed:
                self.current_active_speed = target_speed
        elif self.current_active_speed > target_speed:
            self.current_active_speed -= 0.15
            if self.current_active_speed < target_speed:
                self.current_active_speed = target_speed

        self.score += (self.current_active_speed / FORWARD_SPEED)

        if self.player_x < self.player_target_x:
            self.player_x = min(self.player_target_x, self.player_x + SLIDE_SPEED)
        elif self.player_x > self.player_target_x:
            self.player_x = max(self.player_target_x, self.player_x - SLIDE_SPEED)

        if self.player_x == self.player_target_x:
            if (arcade.key.LEFT in self.keys_held or arcade.key.A in self.keys_held) and self.player_lane > 0:
                self.player_lane -= 1
                self.player_target_x = LANES[self.player_lane]
            elif (arcade.key.RIGHT in self.keys_held or arcade.key.D in self.keys_held) and self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.player_target_x = LANES[self.player_lane]

        # --- Geographical Stages Spawn Logic ---
        if self.spawn_timer >= SPAWN_RATE:

            in_libyan_coast = self.score < 5000
            in_open_mediterranean = 5000 <= self.score < 15000
            in_strait_of_sicily = 15000 <= self.score < 25000
            in_lampedusa_approach = self.score >= 25000

            if in_open_mediterranean or in_strait_of_sicily:
                if len(self.currents) == 0 and random.random() < 0.40:
                    roll = random.random()
                    if roll < 0.30: size = random.randint(1, 3)
                    elif roll < 0.70: size = random.randint(4, 7)
                    else: size = random.randint(8, 10)

                    current_speed = 4.0 - (size * 0.15)
                    start_lane = random.randint(0, NUM_LANES - size)
                    self.currents.append({
                        'start_lane': start_lane,
                        'size': size,
                        'speed': current_speed,
                        'y': HEIGHT + (CURRENT_HEIGHT / 2),
                        'height': CURRENT_HEIGHT
                    })

            if in_libyan_coast:
                num_clumps = random.randint(1, 3)
                base_clump_size = (1, 3)
            elif in_open_mediterranean:
                num_clumps = random.randint(3, 5)
                base_clump_size = (5, 10)
            elif in_strait_of_sicily:
                num_clumps = random.randint(4, 7)
                base_clump_size = (6, 12)
            else:
                num_clumps = random.randint(6, 10)
                base_clump_size = (8, 15)

            for _ in range(num_clumps):
                center_lane = random.randint(10, NUM_LANES - 11)
                center_y = HEIGHT + random.randint(20, 100)
                clump_size = random.randint(base_clump_size[0], base_clump_size[1])

                for _ in range(clump_size):
                    lane_offset = random.randint(-5, 5)
                    y_offset = random.randint(-50, 50)

                    lane_idx = center_lane + lane_offset
                    if 0 <= lane_idx < NUM_LANES:
                        self.obstacles.append([LANES[lane_idx], center_y + y_offset])

            self.spawn_timer = 0

        for curr in self.currents[:]:
            curr['y'] -= self.current_active_speed
            if curr['y'] + (curr['height'] / 2) < 0:
                self.currents.remove(curr)

        for obs in self.obstacles[:]:
            obs[1] -= self.current_active_speed

            if self.invulnerable_timer <= 0:
                if abs(self.player_x - obs[0]) < 6 and abs(obs[1] - PLAYER_Y) < 10:
                    self.energy -= 70.0

                    self.engine_failure_chance += 0.05

                    capacity_loss_percent = random.uniform(0.15, 0.45)
                    self.max_food_percentage *= (1.0 - capacity_loss_percent)

                    if self.food_percentage > self.max_food_percentage:
                        self.food_percentage = self.max_food_percentage

                    self.invulnerable_timer = 1.0
                    self.obstacles.remove(obs)
                    continue

            if obs[1] < -20:
                self.obstacles.remove(obs)

    def on_key_press(self, key, modifiers):
        if self.game_over or self.rescued:
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

        if key == arcade.key.SPACE:
            if self.food_percentage > 0 and self.energy < 100:
                food_to_eat = random.uniform(5.0, 25.0)
                if food_to_eat > self.food_percentage:
                    food_to_eat = self.food_percentage

                self.food_percentage -= food_to_eat
                self.energy_buffer += food_to_eat

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)


if __name__ == "__main__":
    MediterraneanJourney()
    arcade.run()
