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
CURRENT_HEIGHT = 800

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

# --- NPC Passenger Scripts ---
PASSENGER_SCRIPTS = [
    '"I walked across the desert for weeks to escape the military in Eritrea. We can\'t turn back now."',
    '"They burned my village in Darfur. My brother didn\'t make it to the boats. I have to survive for him."',
    '"The smuggler took everything we had left. If this boat sinks, my family has nothing."',
    '"The water is so cold... I\'ve never seen the ocean before today. I\'m terrified."',
    '"The detention camps in Tripoli... the things they did to us there. I\'d rather drown than go back."',
    '"My daughter is asleep. Please, keep the boat steady. Just get us to Italy."',
    '"We have been at sea for so long. Does anyone even know we are out here?"',
    '"I used to be a teacher in Aleppo. Now I am just a shadow on a rubber boat."'
]

class MediterraneanJourney(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Mediterranean Journey")
        arcade.set_background_color((15, 35, 75)) # Deep ocean blue
        self.keys_held = set()

        self.in_menu = True
        self.in_intro = False
        self.reset()
        self.in_menu = True

    def reset(self, start_score=0, cg_test=False):
        """ Resets the game and allows injecting a starting score/test mode """
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

        self.score = start_score
        self.cg_test_mode = cg_test
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

        # --- Storm System Mechanics ---
        self.storm_active = False
        self.storm_duration_timer = 0.0
        self.rain_drops = []

        # --- Passenger Dialogue Mechanics ---
        self.active_dialogue = ""
        self.dialogue_timer = 0.0
        self.next_dialogue_check = random.uniform(45.0, 90.0) # Check every 45-90 seconds

        # State Management
        self.in_menu = False
        self.in_intro = True # Force intro screen before gameplay begins
        self.game_over = False
        self.rescued = False
        self.caught = False

        # --- Day / Night Cycle ---
        self.day_timer = 0.0
        self.morning_duration = 180.0
        self.night_transition_speed = 1200.0

    def on_draw(self):
        self.clear()

        # --- 1. MAIN MENU SCREEN ---
        if self.in_menu:
            arcade.draw_text("MEDITERRANEAN JOURNEY", WIDTH / 2, HEIGHT - 200, arcade.color.WHITE, 40, anchor_x="center", bold=True)
            arcade.draw_text("Select Starting Zone", WIDTH / 2, HEIGHT - 270, arcade.color.LIGHT_GRAY, 22, anchor_x="center")

            menu_options = [
                "1. Libyan Coastal Waters (Score 0)",
                "2. The Empty Sea (Score 1,500)",
                "3. Deep Sea Currents (Score 5,000)",
                "4. The Deceptive Sea (Score 10,000)",
                "5. Patrol Waters (Score 15,000)",
                "6. The Lampedusa Approach (Score 25,000)",
                "7. Coast Guard Test (Continuous Chase)"
            ]

            for i, text in enumerate(menu_options):
                color = arcade.color.LIGHT_STEEL_BLUE if i == 6 else arcade.color.WHITE
                arcade.draw_text(text, WIDTH / 2 - 200, HEIGHT - 350 - (i * 45), color, 18)

            arcade.draw_text("Press 1-7 to Start", WIDTH / 2, HEIGHT - 750, arcade.color.GOLD, 20, anchor_x="center", bold=True)
            return

        # --- 2. INTRO NARRATIVE SCREEN ---
        if self.in_intro:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), arcade.color.BLACK)

            intro_text = (
                "The Central Mediterranean.\n\n"
                "You are at the helm of an overloaded inflatable dinghy, departing from the Libyan coast in the dead of night.\n\n"
                "Behind you are the horrors of the detention camps. Ahead is the perilous open sea, and the hope of Lampedusa.\n"
                "Fuel is low. Rations are scarce. You hold the lives of dozens of desperate people in your hands.\n\n"
                "Watch the waters. Avoid the debris. Conserve your strength."
            )

            arcade.draw_text(intro_text, WIDTH / 2, HEIGHT / 2 + 50, arcade.color.LIGHT_GRAY, 18,
                             width=800, align="center", anchor_x="center", anchor_y="center", multiline=True)

            # Blinking start prompt
            if int(self.day_timer * 2) % 2 == 0:
                arcade.draw_text("Press ENTER to start the engine...", WIDTH / 2, HEIGHT / 2 - 150,
                                 arcade.color.WHITE, 16, anchor_x="center", italic=True)
            return

        # --- 3. NORMAL GAME DRAWING ---

        for curr in self.currents:
            width = curr['size'] * LANE_WIDTH
            center_x = (curr['start_lane'] * LANE_WIDTH) + (width / 2)

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

            arcade.draw_rect_filled(arcade.XYWH(center_x, curr['y'], width, curr['height']), color)

        for obs in self.obstacles:
            arcade.draw_rect_filled(arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 2, LANE_WIDTH - 2), arcade.color.DARK_GRAY)

        for cg in self.coastguards:
            arcade.draw_rect_filled(arcade.XYWH(cg['x'], cg['y'], 12, 28), arcade.color.WHITE)
            arcade.draw_rect_filled(arcade.XYWH(cg['x'], cg['y'] + 4, 12, 6), arcade.color.RED)
            arcade.draw_rect_filled(arcade.XYWH(cg['x'], cg['y'] - 4, 8, 4), arcade.color.DARK_BLUE_GRAY)

            if cg['chasing'] and int(self.day_timer * 4) % 2 == 0:
                arcade.draw_circle_outline(cg['x'], cg['y'], 24, arcade.color.RED, 2)

        # Day/Night Cycle & The Lantern Effect
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
                    self.player_x, PLAYER_Y, radius=r + (band_thickness / 2),
                    color=(0, 0, 0, band_alpha), border_width=band_thickness + 2
                )

            lamp_alpha = int(70 * night_intensity)
            arcade.draw_circle_filled(self.player_x, PLAYER_Y, lamp_radius, (255, 255, 150, lamp_alpha))

        # Storm Overlay
        if self.storm_active:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (5, 10, 25, 120))
            for drop in self.rain_drops:
                arcade.draw_line(drop[0], drop[1], drop[0] - 4, drop[1] - drop[3], (174, 219, 240, 100), 1)

        # Low Energy Vignette
        if self.energy < 15 and not self.game_over and not self.rescued and not self.caught:
            darkness = 1.0 - (max(self.energy, 0) / 15.0)
            alpha = int(245 * darkness)
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, alpha))

        # Pixelated Player Boat
        pontoon_color = arcade.color.SLATE_GRAY
        inside_color = arcade.color.BISTRE

        if self.in_current: pontoon_color = arcade.color.LIGHT_SKY_BLUE
        if self.in_rip_current: pontoon_color = arcade.color.DARK_CYAN
        if self.engine_failed: pontoon_color = arcade.color.FIREBRICK

        start_x = self.player_x - 3
        start_y = PLAYER_Y + 7

        for row_idx, row_str in enumerate(BOAT_ART):
            for col_idx, char in enumerate(row_str):
                if char == 'M':
                    arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), pontoon_color)
                elif char == 'D':
                    arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), inside_color)

        # --- Passenger Dialogue Box ---
        if self.dialogue_timer > 0 and self.active_dialogue != "":
            box_width = 800
            box_height = 80

            # Fade out calculation for the last 2 seconds
            alpha = 200
            text_alpha = 255
            if self.dialogue_timer < 2.0:
                alpha = int(200 * (self.dialogue_timer / 2.0))
                text_alpha = int(255 * (self.dialogue_timer / 2.0))

            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, 120, box_width, box_height), (0, 0, 0, alpha))
            arcade.draw_text(self.active_dialogue, WIDTH / 2, 120, (255, 255, 255, text_alpha), 16,
                             width=760, align="center", anchor_x="center", anchor_y="center", multiline=True, italic=True)

        # UI
        arcade.draw_text(f"RATIONS: {self.food_percentage:.1f}% / {self.max_food_percentage:.1f}%",
                         15, HEIGHT - 35, arcade.color.ORANGE, 16, bold=True)

        if self.energy_buffer > 0:
            arcade.draw_text("REPLENISHING...", 15, HEIGHT - 65, arcade.color.YELLOW, 12, bold=True)

        if self.engine_failed:
            arcade.draw_text("ENGINE FAILURE - DRIFTING", 15, HEIGHT - 85, arcade.color.RED, 14, bold=True)

        if self.storm_active:
            arcade.draw_text("STORM SQUALL", WIDTH - 15, HEIGHT - 65, arcade.color.AZURE, 14, anchor_x="right", bold=True)

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
        # Update day timer for blinking text on intro screen
        if self.in_intro:
            self.day_timer += delta_time
            return

        if self.in_menu or self.game_over or self.rescued or self.caught:
            return

        self.spawn_timer += 1
        self.day_timer += delta_time

        # --- Passenger Dialogue Logic ---
        if self.dialogue_timer > 0:
            self.dialogue_timer -= delta_time
        else:
            self.next_dialogue_check -= delta_time
            if self.next_dialogue_check <= 0:
                # 30% chance to speak when the timer hits
                if random.random() < 0.30:
                    self.active_dialogue = random.choice(PASSENGER_SCRIPTS)
                    self.dialogue_timer = 10.0 # Display for 10 seconds
                self.next_dialogue_check = random.uniform(45.0, 90.0)

        # --- Check Win Condition ---
        if self.score >= 30000:
            self.rescued = True
            return

        # --- TEST MODE: Continuous Coast Guard Spawning ---
        if self.cg_test_mode and len(self.coastguards) == 0:
            self.coastguards.append({
                'x': LANES[random.randint(10, NUM_LANES - 11)],
                'y': HEIGHT + 100,
                'chasing': True
            })

        # --- Storm Timer System ---
        if self.storm_active:
            self.storm_duration_timer -= delta_time
            if self.storm_duration_timer <= 0:
                self.storm_active = False
                self.rain_drops.clear()
            else:
                for drop in self.rain_drops:
                    drop[1] -= drop[2] * delta_time
                    drop[0] -= (drop[2] * 0.1) * delta_time
                    if drop[1] < 0:
                        drop[1] = HEIGHT + random.randint(10, 50)
                        drop[0] = random.randint(0, WIDTH)

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

        base_speed = FORWARD_SPEED + 0.5 if self.storm_active else FORWARD_SPEED
        target_speed = base_speed

        if self.engine_failed:
            target_speed = base_speed * 0.1
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

            in_zone_1 = self.score <= 1500
            in_zone_2 = 1500 < self.score <= 5000
            in_zone_3 = 5000 < self.score <= 10000
            in_zone_4 = 10000 < self.score <= 15000
            in_zone_5 = 15000 < self.score <= 16000
            in_zone_6 = self.score > 16000

            # --- Storm Chance System ---
            if (in_zone_3 or in_zone_4 or in_zone_5) and not self.storm_active and len(self.coastguards) == 0:
                if random.random() < 0.15:
                    self.storm_active = True
                    self.storm_duration_timer = 20.0
                    self.rain_drops = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(800, 1200), random.randint(15, 30)] for _ in range(120)]

            # --- CURRENTS ---
            if in_zone_3 or in_zone_4 or in_zone_5 or in_zone_6 or self.cg_test_mode:
                current_spawn_chance = 0.80 if self.storm_active else 0.40

                if len(self.currents) == 0 and random.random() < current_spawn_chance:
                    is_rip = False
                    if in_zone_4 and random.random() < 0.30 and not self.storm_active:
                        is_rip = True
                        size = random.randint(15, 25)
                        current_speed = base_speed * 0.2
                        current_h = 350
                    else:
                        roll = random.random()
                        if roll < 0.30: size = random.randint(1, 3)
                        elif roll < 0.70: size = random.randint(4, 7)
                        else: size = random.randint(8, 10)
                        speed_multiplier = 1.2 + random.uniform(0.2, 0.5)
                        current_speed = base_speed * speed_multiplier
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
            if in_zone_1 and not self.cg_test_mode:
                num_clumps = 0
                base_clump_size = (0, 0)
                spawn_obstacles = False
            elif in_zone_2:
                if len(self.obstacles) < 5:
                    num_clumps = 1
                    base_clump_size = (1, 2)
                else:
                    spawn_obstacles = False
            elif in_zone_3 or in_zone_5 or self.cg_test_mode:
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

            # --- STANDARD COASTGUARD SPAWN ---
            if in_zone_5 and len(self.coastguards) == 0 and not self.storm_active and not self.cg_test_mode:
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

        # Update Coastguards (Enhanced Physics & Bounding Logic)
        for cg in self.coastguards[:]:
            vis_radius_x = 10 * LANE_WIDTH
            vis_radius_y = 10 * LANE_WIDTH * 2
            if abs(self.player_x - cg['x']) <= vis_radius_x and abs(PLAYER_Y - cg['y']) <= vis_radius_y:
                cg['chasing'] = True

            cg_half_w = 6
            cg_half_h = 14
            obs_half_size = 3

            if cg['chasing']:
                # Horizontal Tracking
                old_x = cg['x']
                if abs(cg['x'] - self.player_x) > 8:
                    cg['x'] += (SLIDE_SPEED * 0.9) if self.player_x > cg['x'] else -(SLIDE_SPEED * 0.9)

                for obs in self.obstacles:
                    if (abs(cg['x'] - obs[0]) < (cg_half_w + obs_half_size) and
                        abs(cg['y'] - obs[1]) < (cg_half_h + obs_half_size)):
                        cg['x'] = old_x
                        break

                # Vertical Logic
                old_y = cg['y']
                if cg['y'] > PLAYER_Y:
                    cg['y'] -= (self.current_active_speed + 1.0)
                    for obs in self.obstacles:
                        if (abs(cg['x'] - obs[0]) < (cg_half_w + obs_half_size) and
                            abs(cg['y'] - obs[1]) < (cg_half_h + obs_half_size)):
                            cg['y'] = old_y - self.current_active_speed
                            break
                else:
                    cg['y'] += 1.5
                    for obs in self.obstacles:
                        if (abs(cg['x'] - obs[0]) < (cg_half_w + obs_half_size) and
                            abs(cg['y'] - obs[1]) < (cg_half_h + obs_half_size)):
                            cg['y'] = old_y - self.current_active_speed
                            break
            else:
                cg['y'] -= self.current_active_speed

            if abs(self.player_x - cg['x']) < 9 and abs(PLAYER_Y - cg['y']) < 19:
                self.caught = True

            if cg['y'] < -200 or cg['y'] > HEIGHT + 500:
                self.coastguards.remove(cg)

        # Move and check obstacles
        for obs in self.obstacles[:]:
            obs[1] -= self.current_active_speed

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
            elif key == arcade.key.KEY_7: self.reset(15001, cg_test=True)
            return

        # --- Handle Intro Screen Input ---
        if self.in_intro:
            if key == arcade.key.ENTER:
                self.in_intro = False
                self.day_timer = 0.0 # Reset timer so day/night cycle starts fresh
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
