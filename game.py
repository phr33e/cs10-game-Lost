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
CURRENT_HEIGHT = 800  # Drastically shortened so they end quickly

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

# --- Custom Pixel Art Boat ---
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
        arcade.set_background_color((15, 35, 75)) # Deep ocean blue
        self.keys_held = set()

        # Start the game in the menu
        self.in_menu = True
        self.reset()
        self.in_menu = True

    def reset(self, start_score=0):
        """ Resets the game and allows injecting a starting score """
        self.player_lane = NUM_LANES // 2
        self.player_x = LANES[self.player_lane]
        self.player_target_x = LANES[self.player_lane]
        self.obstacles = []
        self.currents = []
        self.coastguards = []

        self.in_current = False
        self.in_rip_current = False
        self.current_active_speed = FORWARD_SPEED
        self.spawn_timer = 0

        # Inject the chosen starting score
        self.score = start_score
        self.keys_held.clear()

        # --- Survival Mechanics ---
        self.energy = 100.0
        self.max_food_percentage = 100.0
        self.food_percentage = 100.0
        self.energy_buffer = 0.0
        self.healing_rate = 5.0

        # --- Engine Failure Mechanics ---
        self.engine_failure_chance = 0.01
        self.engine_check_timer = 0.0
        self.next_engine_check = random.uniform(300.0, 420.0)
        self.engine_failed = False
        self.engine_repair_timer = 0.0

        # Turn off all game-stopping states
        self.in_menu = False
        self.game_over = False
        self.rescued = False
        self.caught = False

        # --- Day / Night Cycle ---
        self.day_timer = 0.0
        self.morning_duration = 180.0
        self.night_transition_speed = 1200.0

    def on_draw(self):
        self.clear()

        # --- MAIN MENU SCREEN ---
        if self.in_menu:
            arcade.draw_text("MEDITERRANEAN JOURNEY", WIDTH / 2, HEIGHT - 250, arcade.color.WHITE, 40, anchor_x="center", bold=True)
            arcade.draw_text("Select Starting Zone", WIDTH / 2, HEIGHT - 320, arcade.color.LIGHT_GRAY, 22, anchor_x="center")

            menu_options = [
                "1. Libyan Coastal Waters (Score 0)",
                "2. The Empty Sea (Score 1,500)",
                "3. Deep Sea Currents (Score 5,000)",
                "4. The Deceptive Sea (Score 10,000)",
                "5. Patrol Waters (Score 15,000)",
                "6. The Lampedusa Approach (Score 25,000)"
            ]

            for i, text in enumerate(menu_options):
                arcade.draw_text(text, WIDTH / 2 - 200, HEIGHT - 400 - (i * 45), arcade.color.WHITE, 18)

            arcade.draw_text("Press 1-6 to Start", WIDTH / 2, HEIGHT - 750, arcade.color.GOLD, 20, anchor_x="center", bold=True)
            return

        # --- NORMAL GAME DRAWING ---

        # 1. Draw Currents with Fade In / Fade Out logic
        for curr in self.currents:
            width = curr['size'] * LANE_WIDTH
            center_x = (curr['start_lane'] * LANE_WIDTH) + (width / 2)

            # Calculate alpha modulation based on screen position
            # Fades in over the top 150px and out over the bottom 150px
            max_alpha = 8 if curr.get('is_rip', False) else 12

            if curr['y'] > HEIGHT - 150:
                fade_pct = (HEIGHT - curr['y']) / 150.0
                alpha = int(max_alpha * max(0.0, min(1.0, fade_pct)))
            elif curr['y'] < 150:
                fade_pct = curr['y'] / 150.0
                alpha = int(max_alpha * max(0.0, min(1.0, fade_pct)))
            else:
                alpha = max_alpha

            if curr.get('is_rip', False):
                color = (100, 180, 220, alpha)
            else:
                color = (135, 206, 250, alpha)

            arcade.draw_rect_filled(
                arcade.XYWH(center_x, curr['y'], width, curr['height']), color
            )

        # 2. Draw Obstacles
        for obs in self.obstacles:
            arcade.draw_rect_filled(
                arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 2, LANE_WIDTH - 2),
                arcade.color.DARK_GRAY
            )

        # 3. Draw Coastguards
        for cg in self.coastguards:
            arcade.draw_rect_filled(arcade.XYWH(cg['x'], cg['y'], LANE_WIDTH * 4, LANE_WIDTH * 8), arcade.color.WHITE)
            arcade.draw_rect_filled(arcade.XYWH(cg['x'], cg['y'] + 10, LANE_WIDTH * 4, 6), arcade.color.RED)

            if cg['chasing'] and int(self.day_timer * 4) % 2 == 0:
                arcade.draw_circle_outline(cg['x'], cg['y'], 20, arcade.color.RED, 2)

        # 4. Day/Night Cycle & The Lantern Effect
        night_intensity = 0.0
        if self.day_timer > self.morning_duration:
            time_in_cycle = (self.day_timer - self.morning_duration) % (self.night_transition_speed * 2)
            if time_in_cycle < self.night_transition_speed:
                night_intensity = time_in_cycle / self.night_transition_speed
            else:
                night_intensity = 2.0 - (time_in_cycle / self.night_transition_speed)

        if night_intensity > 0.01 and not self.game_over and not self.rescued and not self.caught:
            lamp_radius = LANE_WIDTH * 5
            current_fov = 1500.0 - ((1500.0 - lamp_radius) * night_intensity)
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

            lamp_alpha = int(70 * night_intensity)
            arcade.draw_circle_filled(
                self.player_x, PLAYER_Y,
                lamp_radius,
                (255, 255, 150, lamp_alpha)
            )

        # 5. Low Energy Vignette
        if self.energy < 15 and not self.game_over and not self.rescued and not self.caught:
            darkness = 1.0 - (max(self.energy, 0) / 15.0)
            alpha = int(245 * darkness)
            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
                (0, 0, 0, alpha)
            )

        # 6. Draw Pixelated Player Boat
        pontoon_color = arcade.color.SLATE_GRAY
        inside_color = arcade.color.BISTRE

        if self.in_current:
            pontoon_color = arcade.color.LIGHT_SKY_BLUE
        if self.in_rip_current:
            pontoon_color = arcade.color.DARK_CYAN
        if self.engine_failed:
            pontoon_color = arcade.color.FIREBRICK

        start_x = self.player_x - 3
        start_y = PLAYER_Y + 7

        for row_idx, row_str in enumerate(BOAT_ART):
            for col_idx, char in enumerate(row_str):
                if char == 'M':
                    arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), pontoon_color)
                elif char == 'D':
                    arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), inside_color)

        # 7. Draw UI (Changed to RATIONS, instruction prompt removed)
        arcade.draw_text(f"RATIONS: {self.food_percentage:.1f}% / {self.max_food_percentage:.1f}%",
                         15, HEIGHT - 35, arcade.color.ORANGE, 16, bold=True)

        if self.energy_buffer > 0:
            arcade.draw_text("REPLENISHING...", 15, HEIGHT - 65, arcade.color.YELLOW, 12, bold=True)

        if self.engine_failed:
            arcade.draw_text("ENGINE FAILURE - DRIFTING", 15, HEIGHT - 85, arcade.color.RED, 14, bold=True)

        if self.in_current and not self.engine_failed and not self.in_rip_current:
            multiplier = self.current_active_speed / FORWARD_SPEED
            arcade.draw_text(f"CURRENT CAUGHT! x{multiplier:.2f} SPD", WIDTH - 15, HEIGHT - 35,
                             arcade.color.LIGHT_SKY_BLUE, 16, anchor_x="right", bold=True)
        elif self.in_rip_current and not self.engine_failed:
            arcade.draw_text("TRAPPED IN RIP CURRENT!", WIDTH - 15, HEIGHT - 35,
                             arcade.color.DARK_CYAN, 16, anchor_x="right", bold=True)

        # End States
        if self.rescued:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 200))
            arcade.draw_text("LAMPEDUSA COAST SIGHTED. YOU SURVIVED.", WIDTH / 2, HEIGHT / 2, arcade.color.GOLD, 24, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to return to Menu", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")

        elif self.caught:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 230))
            arcade.draw_text("INTERCEPTED BY COASTGUARD", WIDTH / 2, HEIGHT / 2, arcade.color.RED, 26, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to return to Menu", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")

        elif self.game_over:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), arcade.color.BLACK)
            arcade.draw_text("THE JOURNEY HAS ENDED", WIDTH / 2, HEIGHT / 2, arcade.color.RED, 30, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to return to Menu", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")

    def on_update(self, delta_time):
        if self.in_menu or self.game_over or self.rescued or self.caught:
            return

        self.spawn_timer += 1
        self.day_timer += delta_time

        # --- Check Win Condition ---
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

        # --- Check Currents & Determine Target Speed ---
        self.in_current = False
        self.in_rip_current = False
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
                    if curr.get('is_rip', False):
                        self.in_rip_current = True
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

        # --- SEAMLESS GEOGRAPHICAL ZONES LOGIC ---
        if self.spawn_timer >= SPAWN_RATE:

            # Adjusted scoring ranges so they fit flush back-to-back
            in_zone_1 = self.score <= 1500
            in_zone_2 = 1500 < self.score <= 5000
            in_zone_3 = 5000 < self.score <= 10000
            in_zone_4 = 10000 < self.score <= 15000
            in_zone_5 = 15000 < self.score <= 16000
            in_zone_6 = self.score > 16000

            # --- CURRENTS ---
            if in_zone_3 or in_zone_4 or in_zone_5 or in_zone_6:
                if len(self.currents) == 0 and random.random() < 0.40:

                    is_rip = False
                    if in_zone_4 and random.random() < 0.30:
                        is_rip = True
                        size = random.randint(15, 25)
                        current_speed = FORWARD_SPEED * 0.2
                        current_h = 350 # Sinks/ends much quicker
                    else:
                        roll = random.random()
                        if roll < 0.30: size = random.randint(1, 3)
                        elif roll < 0.70: size = random.randint(4, 7)
                        else: size = random.randint(8, 10)
                        speed_multiplier = 1.0 + random.uniform(0.2, 0.5)
                        current_speed = FORWARD_SPEED * speed_multiplier
                        current_h = CURRENT_HEIGHT

                    start_lane = random.randint(0, NUM_LANES - size)
                    self.currents.append({
                        'start_lane': start_lane,
                        'size': size,
                        'speed': current_speed,
                        'y': HEIGHT + (current_h / 2),
                        'height': current_h,
                        'is_rip': is_rip
                    })

            # --- OBSTACLES ---
            spawn_obstacles = True
            if in_zone_1:
                num_clumps = 0
                base_clump_size = (0, 0)
                spawn_obstacles = False
            elif in_zone_2:
                if len(self.obstacles) < 5:
                    num_clumps = 1
                    base_clump_size = (1, 2)
                else:
                    spawn_obstacles = False
            elif in_zone_3 or in_zone_5:
                num_clumps = random.randint(2, 4)
                base_clump_size = (3, 6)
            elif in_zone_4:
                if random.random() < 0.3:
                    num_clumps = 1
                    base_clump_size = (40, 60)
                else:
                    spawn_obstacles = False
            else:
                num_clumps = random.randint(6, 10)
                base_clump_size = (8, 15)

            if spawn_obstacles:
                for _ in range(num_clumps):
                    center_lane = random.randint(10, NUM_LANES - 11)
                    center_y = HEIGHT + random.randint(20, 100)
                    clump_size = random.randint(base_clump_size[0], base_clump_size[1])

                    offset_range = 25 if in_zone_4 else 5

                    for _ in range(clump_size):
                        lane_offset = random.randint(-offset_range, offset_range)
                        y_offset = random.randint(-50, 50)

                        lane_idx = center_lane + lane_offset
                        if 0 <= lane_idx < NUM_LANES:
                            self.obstacles.append([LANES[lane_idx], center_y + y_offset])

            # --- COASTGUARD ---
            if in_zone_5 and len(self.coastguards) == 0:
                if random.random() < 0.2:
                    self.coastguards.append({
                        'x': LANES[random.randint(10, NUM_LANES - 11)],
                        'y': HEIGHT + 400,
                        'chasing': False
                    })

            self.spawn_timer = 0

        # Move currents
        for curr in self.currents[:]:
            curr['y'] -= self.current_active_speed
            if curr['y'] + (curr['height'] / 2) < 0:
                self.currents.remove(curr)

        # Update Coastguards
        for cg in self.coastguards[:]:
            vis_radius_x = 10 * LANE_WIDTH
            vis_radius_y = 10 * LANE_WIDTH * 2

            if abs(self.player_x - cg['x']) <= vis_radius_x and abs(PLAYER_Y - cg['y']) <= vis_radius_y:
                cg['chasing'] = True

            if cg['chasing']:
                if cg['x'] < self.player_x: cg['x'] += SLIDE_SPEED * 1.5
                if cg['x'] > self.player_x: cg['x'] -= SLIDE_SPEED * 1.5

                if cg['y'] > PLAYER_Y: cg['y'] -= ((FORWARD_SPEED * 1.1) + self.current_active_speed)
                if cg['y'] < PLAYER_Y: cg['y'] += (FORWARD_SPEED * 1.1)
            else:
                cg['y'] -= self.current_active_speed

            if abs(self.player_x - cg['x']) < 15 and abs(PLAYER_Y - cg['y']) < 15:
                self.caught = True

            if cg['y'] < -200:
                self.coastguards.remove(cg)

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= self.current_active_speed

            # --- Unforgiving Collision (No I-Frames) ---
            if abs(self.player_x - obs[0]) < 6 and abs(obs[1] - PLAYER_Y) < 10:
                self.energy -= 70.0
                self.engine_failure_chance += 0.05

                capacity_loss_percent = random.uniform(0.15, 0.45)
                self.max_food_percentage *= (1.0 - capacity_loss_percent)
                if self.food_percentage > self.max_food_percentage:
                    self.food_percentage = self.max_food_percentage

                self.obstacles.remove(obs)
                continue

            if obs[1] < -20:
                self.obstacles.remove(obs)

    def on_key_press(self, key, modifiers):
        # --- Handle Menu Input ---
        if self.in_menu:
            if key == arcade.key.KEY_1: self.reset(0)
            elif key == arcade.key.KEY_2: self.reset(1501)
            elif key == arcade.key.KEY_3: self.reset(5001)
            elif key == arcade.key.KEY_4: self.reset(10001)
            elif key == arcade.key.KEY_5: self.reset(15001)
            elif key == arcade.key.KEY_6: self.reset(25001)
            return

        # --- Handle End State Returns ---
        if self.game_over or self.rescued or self.caught:
            if key == arcade.key.ENTER:
                self.in_menu = True
            return

        # --- Handle Gameplay Input ---
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
