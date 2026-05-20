import arcade
import random
import math

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

# --- Deep Narrative Passenger Scripts ---
PASSENGER_SCRIPTS = [
    [
        '"Driver... do you think the coast guard is actually looking for us?"',
        '"My name is Amir. I used to teach mathematics in Aleppo. Now I am sitting in bilge water, praying to a sky that feels empty."',
        '"My daughter, Noor, is sleeping against my chest. I told her we were going on a grand adventure on a big ship."',
        '"When she saw this inflatable raft on the beach... she cried. But we couldn\'t stay in Libya. You know what happens there."',
        '"Just keep the bow steady against the waves. If we make it to Lampedusa, she can go to school again."'
    ],
    [
        '"I can\'t feel my legs anymore. How much longer until we see land?"',
        '"My name is Yonas. I left Eritrea two years ago to avoid the military conscription. It\'s essentially slavery. I walked across the Sahara to get here."',
        '"I saw people left behind in the sand because they couldn\'t keep up with the smuggler\'s trucks. But Libya was worse."',
        '"The militias in Bani Walid locked us in a warehouse for six months. They tortured us while on the phone with our families to extort ransom."',
        '"This boat is our only way out. I spent my life savings for a spot on this rubber floor. Please don\'t let us die out here."'
    ],
    [
        '"The engine sounds terrible. It\'s struggling. Did they give us enough mixed fuel?"',
        '"My name is Fatima. The smuggler on the beach... he pointed a rifle at us and forced 120 of us onto a boat meant for 40."',
        '"My husband tried to argue. He said it wasn\'t safe. The smuggler hit him with the rifle butt and told us to get on or die on the sand."',
        '"We left Sudan because our village in Darfur was burned to the ground. We have been running for three years."',
        '"I am so tired of running. I just want a place where my family can sleep without listening for gunfire."'
    ],
    [
        '"Look at the water. My name is Tariq; I was a fisherman back home in Gaza. I know the sea. This sea is angry tonight."',
        '"We shouldn\'t be out here in a rubber dinghy. The pontoon is already losing air on the starboard side."',
        '"But what choice did we have? The detention center guards in Tripoli were selling people into forced labor."',
        '"I\'d rather take my chances with an angry sea than a cruel man. The sea, at least, doesn\'t hate us. It\'s just water."',
        '"Watch the swells. Hit them straight on, or they will flip us. May God protect us."'
    ]
]

ZONE_FACTS = {
    1: "ZONE 1: LIBYAN COASTAL WATERS\n\nFACT: The Central Mediterranean is considered the deadliest migration route in the world.\nSmugglers often launch overcrowded, unseaworthy vessels under the cover of darkness.",
    2: "ZONE 2: THE EMPTY SEA\n\nFACT: Many vessels used are flimsy rubber dinghies or rotting wooden fishing boats,\nfrequently provided with just enough fuel to reach international waters.",
    3: "ZONE 3: DEEP SEA CURRENTS\n\nFACT: According to the UN's International Organization for Migration (IOM),\nover 23,000 people have gone missing or died attempting this crossing since 2014.",
    4: "ZONE 4: THE DECEPTIVE SEA\n\nFACT: Without navigational equipment, migrants rely on the stars or a cheap compass.\nA single storm or error can mean drifting aimlessly until supplies run out.",
    5: "ZONE 5: PATROL WATERS\n\nFACT: Under international maritime law, any vessel in distress must be rescued.\nHowever, political disputes and the restriction of NGO rescue ships have left many to perish at sea.",
    6: "ZONE 6: THE LAMPEDUSA APPROACH\n\nFACT: For those who survive the harrowing journey, landing in Europe is only the beginning\nof a long, complex asylum process."
}

ENGINE_FAILURE_FACT = "FACT: Engine failure is a leading cause of tragedy. Smugglers often provide cheap, inadequate outboard motors.\nWhen they fail, the boat becomes a drifting coffin, leaving passengers to succumb to the elements."


class MediterraneanJourney(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Mediterranean Journey")
        arcade.set_background_color((15, 35, 75))
        self.keys_held = set()

        # State Machine Flags
        self.state = "MENU" # States: MENU, INTRO, CHECKPOINT, PLAYING, RESCUED, CAUGHT, GAMEOVER

        self.reset()
        self.state = "MENU"

    def reset(self, start_score=0, cg_test=False, current_test=False, engine_test=False):
        self.player_lane = NUM_LANES // 2
        self.player_x = LANES[self.player_lane]
        self.player_target_x = LANES[self.player_lane]
        self.obstacles = []
        self.currents = []
        self.coastguards = []
        self.waves = []
        self.beach_y = None

        self.in_current = False
        self.in_rip_current = False
        self.current_active_speed = FORWARD_SPEED
        self.spawn_timer = 0

        # Scoring & Modes
        self.score = start_score
        self.cg_test_mode = cg_test
        self.current_test_mode = current_test
        self.engine_test_mode = engine_test
        self.keys_held.clear()

        # Survival Mechanics
        self.energy = 100.0
        self.max_food_percentage = 100.0
        self.food_percentage = 100.0
        self.energy_buffer = 0.0
        self.healing_rate = 5.0

        # Engine Mechanics
        self.engine_failure_chance = 0.01
        self.engine_check_timer = 0.0
        self.next_engine_check = random.uniform(300.0, 420.0)
        self.engine_failed = False
        self.stuck_on_rock = False

        # Storm Mechanics
        self.storm_active = False
        self.storm_duration_timer = 0.0
        self.rain_drops = []

        # Narrative Systems
        self.current_passenger_script = None
        self.passenger_dialogue_index = 0
        self.next_dialogue_check = random.uniform(30.0, 60.0)

        # Zone tracking for checkpoints
        self.current_zone = 1
        self.active_fact = ZONE_FACTS[1]

        # Day / Night Cycle
        self.day_timer = 0.0
        self.morning_duration = 180.0
        self.night_transition_speed = 1200.0

        # Trigger immediate engine failure if testing
        if self.engine_test_mode:
            self.engine_failed = True

        self.update_zone(self.score, initialize=True)

    def update_zone(self, current_score, initialize=False):
        # 5x Scaled Zone Thresholds
        new_zone = 1
        if current_score >= 80000: new_zone = 6
        elif current_score >= 75000: new_zone = 5
        elif current_score >= 50000: new_zone = 4
        elif current_score >= 25000: new_zone = 3
        elif current_score >= 7500: new_zone = 2

        if new_zone > self.current_zone or (initialize and new_zone >= 1):
            self.current_zone = new_zone
            self.active_fact = ZONE_FACTS[self.current_zone]
            # When hitting a new zone naturally, trigger the checkpoint slideshow
            if not initialize:
                self.state = "CHECKPOINT"

    def on_draw(self):
        self.clear()

        # --- 1. MAIN MENU SCREEN ---
        if self.state == "MENU":
            arcade.draw_text("MEDITERRANEAN JOURNEY", WIDTH / 2, HEIGHT - 200, arcade.color.WHITE, 40, anchor_x="center", bold=True)
            arcade.draw_text("Select Starting Zone or Test Mode", WIDTH / 2, HEIGHT - 270, arcade.color.LIGHT_GRAY, 22, anchor_x="center")

            menu_options = [
                "1. Libyan Coastal Waters (Score 0)",
                "2. The Empty Sea (Score 7,500)",
                "3. Deep Sea Currents (Score 25,000)",
                "4. The Deceptive Sea (Score 50,000)",
                "5. Patrol Waters (Score 75,000)",
                "6. The Lampedusa Approach (Score 80,000)",
                "7. Coast Guard Chase Test",
                "8. Current Mechanics Test",
                "9. Fatal Engine Failure Test"
            ]

            for i, text in enumerate(menu_options):
                color = arcade.color.LIGHT_STEEL_BLUE if i >= 6 else arcade.color.WHITE
                arcade.draw_text(text, WIDTH / 2 - 200, HEIGHT - 330 - (i * 40), color, 18)

            arcade.draw_text("Press 1-9 to Start", WIDTH / 2, HEIGHT - 750, arcade.color.GOLD, 20, anchor_x="center", bold=True)
            return

        # --- 2. INTRO NARRATIVE SCREEN ---
        if self.state == "INTRO":
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
            if int(self.day_timer * 2) % 2 == 0:
                arcade.draw_text("Press ENTER to continue...", WIDTH / 2, HEIGHT / 2 - 150, arcade.color.WHITE, 16, anchor_x="center", italic=True)
            return

        # --- 3. CHECKPOINT SLIDESHOW SCREEN ---
        if self.state == "CHECKPOINT":
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), arcade.color.BLACK)
            arcade.draw_text(self.active_fact, WIDTH / 2, HEIGHT / 2, arcade.color.LIGHT_GRAY, 22,
                             width=900, align="center", anchor_x="center", anchor_y="center", multiline=True)
            if int(self.day_timer * 2) % 2 == 0:
                arcade.draw_text("Press ENTER to start the engine...", WIDTH / 2, HEIGHT / 2 - 200, arcade.color.WHITE, 16, anchor_x="center", italic=True)
            return

        # --- 4. NORMAL GAME DRAWING ---

        # Currents (Flowing Lines Visual)
        for curr in self.currents:
            width = curr['size'] * LANE_WIDTH
            center_x = (curr['start_lane'] * LANE_WIDTH) + (width / 2)

            # Fade logic based on vertical position
            max_alpha = 40 if curr.get('is_rip', False) else 70
            if curr['y'] > HEIGHT - 150:
                fade_pct = (HEIGHT - curr['y']) / 150.0
                alpha = int(max_alpha * max(0.0, min(1.0, fade_pct)))
            elif curr['y'] < 150:
                fade_pct = curr['y'] / 150.0
                alpha = int(max_alpha * max(0.0, min(1.0, fade_pct)))
            else:
                alpha = max_alpha

            color = (100, 180, 220, alpha) if curr.get('is_rip', False) else (255, 255, 255, alpha)

            # Draw flowing streaks within the current box
            left_edge = center_x - (width / 2)
            num_streaks = curr['size'] // 2 + 1
            for i in range(num_streaks):
                streak_x = left_edge + (i * 15) + 5
                # Flowing offset using day_timer
                flow_offset = (self.day_timer * 300 + i * 40) % curr['height']
                streak_y_top = (curr['y'] + curr['height'] / 2) - flow_offset
                streak_y_bottom = streak_y_top - 60

                # Keep streaks within bounds
                if streak_y_bottom < curr['y'] - curr['height'] / 2:
                    streak_y_bottom = curr['y'] - curr['height'] / 2

                if streak_y_top > streak_y_bottom:
                    arcade.draw_line(streak_x, streak_y_top, streak_x, streak_y_bottom, color, 2)

        # Beach (Lampedusa)
        if self.beach_y is not None:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, self.beach_y + 1000, WIDTH, 2000), (220, 200, 150))

        # Storm Waves
        for wave in self.waves:
            # Drawn as a wide, frothy blue/white crest
            arcade.draw_rect_filled(arcade.XYWH(wave[0], wave[1], wave[2], 12), (180, 220, 255, 200))
            arcade.draw_rect_filled(arcade.XYWH(wave[0], wave[1] + 4, wave[2] - 10, 4), (255, 255, 255, 200))

        # Obstacles
        for obs in self.obstacles:
            arcade.draw_rect_filled(arcade.XYWH(obs[0], obs[1], LANE_WIDTH - 2, LANE_WIDTH - 2), arcade.color.DARK_GRAY)

        # Coastguards
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
            if time_in_cycle < self.night_transition_speed: night_intensity = time_in_cycle / self.night_transition_speed
            else: night_intensity = 2.0 - (time_in_cycle / self.night_transition_speed)

        if night_intensity > 0.01 and self.state == "PLAYING":
            lamp_radius = LANE_WIDTH * 5
            current_fov = 1500.0 - ((1500.0 - lamp_radius) * night_intensity)
            num_bands = 15
            max_radius = 2000
            band_thickness = (max_radius - current_fov) / num_bands
            for i in range(num_bands):
                r = current_fov + (i * band_thickness)
                band_alpha = int((255 * night_intensity) * ((i + 1) / num_bands))
                arcade.draw_circle_outline(self.player_x, PLAYER_Y, radius=r + (band_thickness / 2),
                                           color=(0, 0, 0, band_alpha), border_width=band_thickness + 2)
            lamp_alpha = int(70 * night_intensity)
            arcade.draw_circle_filled(self.player_x, PLAYER_Y, lamp_radius, (255, 255, 150, lamp_alpha))

        # Storm Overlay
        if self.storm_active:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (5, 10, 25, 120))
            for drop in self.rain_drops:
                arcade.draw_line(drop[0], drop[1], drop[0] - 4, drop[1] - drop[3], (174, 219, 240, 100), 1)

        # Low Energy Vignette
        if self.energy < 15 and self.state == "PLAYING":
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
                if char == 'M': arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), pontoon_color)
                elif char == 'D': arcade.draw_rect_filled(arcade.XYWH(start_x + col_idx, start_y - row_idx, 1, 1), inside_color)

        # --- Passenger Dialogue Box & Prompt ---
        if self.current_passenger_script is not None:
            box_width = 850
            box_height = 110

            # Semi-transparent background for story text
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, 160, box_width, box_height), (0, 0, 0, 230))

            current_text = self.current_passenger_script[self.passenger_dialogue_index]
            arcade.draw_text(current_text, WIDTH / 2, 175, arcade.color.WHITE, 16,
                             width=800, align="center", anchor_x="center", anchor_y="center", multiline=True, italic=True)

            # Instructions specifically placed BELOW the text box in white
            instruction_y = 160 - (box_height / 2) - 20
            arcade.draw_text("Space bar to continue (Costs 5% Rations)     L to ignore",
                             WIDTH / 2, instruction_y, arcade.color.WHITE, 14, anchor_x="center")

        # --- UI ---
        arcade.draw_text(f"RATIONS: {self.food_percentage:.1f}% / {self.max_food_percentage:.1f}%",
                         15, HEIGHT - 35, arcade.color.ORANGE, 16, bold=True)

        if self.engine_failed:
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT - 60, WIDTH, 80), (0, 0, 0, 200))
            arcade.draw_text(ENGINE_FAILURE_FACT, WIDTH / 2, HEIGHT - 60, arcade.color.RED, 14,
                             width=900, align="center", anchor_x="center", anchor_y="center", multiline=True, bold=True)

        if self.energy_buffer > 0 and self.current_passenger_script is None:
            arcade.draw_text("REPLENISHING...", 15, HEIGHT - 65, arcade.color.YELLOW, 12, bold=True)

        if self.storm_active and not self.engine_failed:
            arcade.draw_text("STORM SQUALL", WIDTH - 15, HEIGHT - 65, arcade.color.AZURE, 14, anchor_x="right", bold=True)

        if self.in_current and not self.engine_failed and not self.in_rip_current:
            multiplier = self.current_active_speed / FORWARD_SPEED
            arcade.draw_text(f"CURRENT CAUGHT! x{multiplier:.2f} SPD", WIDTH - 15, HEIGHT - 35, arcade.color.LIGHT_SKY_BLUE, 16, anchor_x="right", bold=True)
        elif self.in_rip_current and not self.engine_failed:
            arcade.draw_text("TRAPPED IN RIP CURRENT!", WIDTH - 15, HEIGHT - 35, arcade.color.DARK_CYAN, 16, anchor_x="right", bold=True)

        # End States
        if self.state == "RESCUED":
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 200))
            arcade.draw_text("LAMPEDUSA COAST SIGHTED. YOU SURVIVED.", WIDTH / 2, HEIGHT / 2, arcade.color.GOLD, 24, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to return to Menu", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")
        elif self.state == "CAUGHT":
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 230))
            arcade.draw_text("INTERCEPTED BY COASTGUARD", WIDTH / 2, HEIGHT / 2, arcade.color.RED, 26, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to return to Menu", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")
        elif self.state == "GAMEOVER":
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), arcade.color.BLACK)
            arcade.draw_text("THE JOURNEY HAS ENDED", WIDTH / 2, HEIGHT / 2, arcade.color.RED, 30, anchor_x="center", bold=True)
            arcade.draw_text("Press ENTER to return to Menu", WIDTH / 2, HEIGHT / 2 - 40, arcade.color.WHITE, 20, anchor_x="center")

    def on_update(self, delta_time):
        # Only update timers if waiting on a static screen
        if self.state in ["INTRO", "CHECKPOINT"]:
            self.day_timer += delta_time
            return

        if self.state != "PLAYING":
            return

        self.spawn_timer += 1
        self.day_timer += delta_time

        self.update_zone(self.score)

        # --- Lampedusa Beach Win Condition ---
        if self.score >= 150000 and self.beach_y is None:
            self.beach_y = HEIGHT + 200 # Spawn just above screen

        if self.beach_y is not None:
            self.beach_y -= self.current_active_speed
            if self.beach_y <= PLAYER_Y:
                self.state = "RESCUED"
                return

        # --- Passenger Dialogue Logic ---
        if self.current_passenger_script is None:
            self.next_dialogue_check -= delta_time
            if self.next_dialogue_check <= 0:
                if random.random() < 0.25:
                    self.current_passenger_script = random.choice(PASSENGER_SCRIPTS)
                    self.passenger_dialogue_index = 0
                self.next_dialogue_check = random.uniform(30.0, 60.0)

        # --- TEST MODE: Continuous Coast Guard Spawning ---
        if self.cg_test_mode and len(self.coastguards) == 0:
            self.coastguards.append({
                'x': LANES[random.randint(10, NUM_LANES - 11)],
                'y': HEIGHT + 100,
                'chasing': True
            })

        # --- Storm & Wave System ---
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

        # Wave Logic (Spawned below in spawn loop, updated here)
        for w in self.waves[:]:
            # Waves move downwards faster than the background flow
            w[1] -= (self.current_active_speed + w[3])

            # Wave Collision (energy damage only)
            if abs(self.player_x - w[0]) < (w[2] / 2 + 6) and abs(PLAYER_Y - w[1]) < 10:
                self.energy -= 20.0
                self.waves.remove(w)
            elif w[1] < -50:
                self.waves.remove(w)

        # --- Fatal Engine Failure Logic ---
        if not self.engine_failed and not self.current_test_mode:
            self.engine_check_timer += delta_time
            if self.engine_check_timer >= self.next_engine_check:
                if random.random() < self.engine_failure_chance:
                    self.engine_failed = True
                self.engine_check_timer = 0.0
                self.next_engine_check = random.uniform(300.0, 420.0)

        if self.energy_buffer > 0:
            heal_step = self.healing_rate * delta_time
            if heal_step > self.energy_buffer: heal_step = self.energy_buffer
            self.energy_buffer -= heal_step
            self.energy += heal_step
            if self.energy > 100.0:
                self.energy = 100.0
                self.energy_buffer = 0.0

        self.energy -= (1.0 / 60.0) * delta_time
        if self.energy <= 0:
            self.state = "GAMEOVER"

        self.in_current = False
        self.in_rip_current = False

        base_speed = FORWARD_SPEED + 0.5 if self.storm_active else FORWARD_SPEED
        target_speed = base_speed

        if self.engine_failed:
            if self.stuck_on_rock: target_speed = 0.0
            else: target_speed = 0.05
        else:
            for curr in self.currents:
                zone_left = curr['start_lane'] * LANE_WIDTH
                zone_right = (curr['start_lane'] + curr['size']) * LANE_WIDTH
                zone_bottom = curr['y'] - curr['height'] / 2
                zone_top = curr['y'] + curr['height'] / 2

                if zone_left <= self.player_x <= zone_right and zone_bottom <= PLAYER_Y <= zone_top:
                    self.in_current = True
                    target_speed = curr['speed']
                    if curr.get('is_rip', False): self.in_rip_current = True
                    break

        if self.current_active_speed < target_speed:
            self.current_active_speed += 0.15
            if self.current_active_speed > target_speed: self.current_active_speed = target_speed
        elif self.current_active_speed > target_speed:
            self.current_active_speed -= 0.15
            if self.current_active_speed < target_speed: self.current_active_speed = target_speed

        self.score += (self.current_active_speed / FORWARD_SPEED)

        if not self.engine_failed:
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
        if self.spawn_timer >= SPAWN_RATE and not self.stuck_on_rock:

            in_zone_1 = self.score <= 7500
            in_zone_2 = 7500 < self.score <= 25000
            in_zone_3 = 25000 < self.score <= 50000
            in_zone_4 = 50000 < self.score <= 75000
            in_zone_5 = 75000 < self.score <= 80000
            in_zone_6 = self.score > 80000

            if (in_zone_3 or in_zone_4 or in_zone_5) and not self.storm_active and len(self.coastguards) == 0 and not self.current_test_mode:
                if random.random() < 0.15:
                    self.storm_active = True
                    self.storm_duration_timer = 20.0
                    self.rain_drops = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(800, 1200), random.randint(15, 30)] for _ in range(120)]

            # Currents
            if in_zone_3 or in_zone_4 or in_zone_5 or in_zone_6 or self.cg_test_mode or self.current_test_mode:
                current_spawn_chance = 0.80 if self.storm_active else 0.40
                if self.current_test_mode: current_spawn_chance = 0.90 # Test mode spam

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

            # Obstacles & Waves
            spawn_obstacles = True
            if in_zone_1 or self.cg_test_mode or self.current_test_mode:
                num_clumps = 0
                base_clump_size = (0, 0)
                spawn_obstacles = False
            elif in_zone_2:
                if len(self.obstacles) < 5:
                    num_clumps = 1
                    base_clump_size = (1, 2)
                else: spawn_obstacles = False
            elif in_zone_3 or in_zone_5:
                num_clumps = random.randint(2, 4)
                base_clump_size = (3, 6)
            elif in_zone_4:
                if random.random() < 0.3:
                    num_clumps = 1
                    base_clump_size = (40, 60)
                else: spawn_obstacles = False
            else:
                num_clumps = random.randint(6, 10)
                base_clump_size = (8, 15)

            if spawn_obstacles:
                # During storms, 20% chance to spawn a moving wave instead of a rock clump
                if self.storm_active and random.random() < 0.20:
                    wave_width = random.randint(30, 80)
                    wave_x = random.randint(0, WIDTH)
                    wave_y = HEIGHT + random.randint(20, 100)
                    wave_speed = random.uniform(1.0, 2.5) # Moves downward faster than normal flow
                    self.waves.append([wave_x, wave_y, wave_width, wave_speed])
                else:
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

            # Coastguards
            if in_zone_5 and len(self.coastguards) == 0 and not self.storm_active and not self.cg_test_mode and not self.current_test_mode:
                if random.random() < 0.2:
                    self.coastguards.append({
                        'x': LANES[random.randint(10, NUM_LANES - 11)],
                        'y': HEIGHT + 400,
                        'chasing': False
                    })

            self.spawn_timer = 0

        for curr in self.currents[:]:
            curr['y'] -= self.current_active_speed
            if curr['y'] + (curr['height'] / 2) < 0:
                self.currents.remove(curr)

        for cg in self.coastguards[:]:
            vis_radius_x = 10 * LANE_WIDTH
            vis_radius_y = 10 * LANE_WIDTH * 2
            if abs(self.player_x - cg['x']) <= vis_radius_x and abs(PLAYER_Y - cg['y']) <= vis_radius_y:
                cg['chasing'] = True

            cg_half_w = 6
            cg_half_h = 14
            obs_half_size = 3

            if cg['chasing']:
                old_x = cg['x']
                if abs(cg['x'] - self.player_x) > 8:
                    cg['x'] += (SLIDE_SPEED * 0.9) if self.player_x > cg['x'] else -(SLIDE_SPEED * 0.9)

                for obs in self.obstacles:
                    if (abs(cg['x'] - obs[0]) < (cg_half_w + obs_half_size) and abs(cg['y'] - obs[1]) < (cg_half_h + obs_half_size)):
                        cg['x'] = old_x
                        break

                old_y = cg['y']
                if cg['y'] > PLAYER_Y:
                    cg['y'] -= (self.current_active_speed + 1.0)
                    for obs in self.obstacles:
                        if (abs(cg['x'] - obs[0]) < (cg_half_w + obs_half_size) and abs(cg['y'] - obs[1]) < (cg_half_h + obs_half_size)):
                            cg['y'] = old_y - self.current_active_speed
                            break
                else:
                    cg['y'] += 1.5
                    for obs in self.obstacles:
                        if (abs(cg['x'] - obs[0]) < (cg_half_w + obs_half_size) and abs(cg['y'] - obs[1]) < (cg_half_h + obs_half_size)):
                            cg['y'] = old_y - self.current_active_speed
                            break
            else:
                cg['y'] -= self.current_active_speed

            if abs(self.player_x - cg['x']) < 9 and abs(PLAYER_Y - cg['y']) < 19:
                self.state = "CAUGHT"

            if cg['y'] < -200 or cg['y'] > HEIGHT + 500:
                self.coastguards.remove(cg)

        for obs in self.obstacles[:]:
            obs[1] -= self.current_active_speed

            if abs(self.player_x - obs[0]) < 6 and abs(obs[1] - PLAYER_Y) < 10:
                if self.engine_failed:
                    self.stuck_on_rock = True
                else:
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
        if self.state == "MENU":
            if key == arcade.key.KEY_1: self.reset(0)
            elif key == arcade.key.KEY_2: self.reset(7501)
            elif key == arcade.key.KEY_3: self.reset(25001)
            elif key == arcade.key.KEY_4: self.reset(50001)
            elif key == arcade.key.KEY_5: self.reset(75001)
            elif key == arcade.key.KEY_6: self.reset(80001)
            elif key == arcade.key.KEY_7: self.reset(75001, cg_test=True)
            elif key == arcade.key.KEY_8: self.reset(25001, current_test=True)
            elif key == arcade.key.KEY_9: self.reset(0, engine_test=True)

            # Immediately queue the Intro screen after selection
            self.state = "INTRO"
            return

        if self.state == "INTRO":
            if key == arcade.key.ENTER:
                self.day_timer = 0.0
                # Move to the first checkpoint slideshow to establish context
                self.state = "CHECKPOINT"
            return

        if self.state == "CHECKPOINT":
            if key == arcade.key.ENTER:
                self.day_timer = 0.0
                self.state = "PLAYING"
            return

        if self.state in ["GAMEOVER", "RESCUED", "CAUGHT"]:
            if key == arcade.key.ENTER:
                self.reset()
                self.state = "MENU"
            return

        if not self.engine_failed:
            if key in [arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D]:
                self.keys_held.add(key)

        if key == arcade.key.L:
            self.current_passenger_script = None

        if key == arcade.key.SPACE:
            if self.current_passenger_script is not None:
                if self.food_percentage >= 5.0:
                    self.food_percentage -= 5.0
                    self.passenger_dialogue_index += 1

                    if self.passenger_dialogue_index >= len(self.current_passenger_script):
                        self.current_passenger_script = None
            else:
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
