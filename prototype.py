import math
import random

import arcade


# --- Screen configuration ---
NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 600
TITLE = "The Journey - Lampedusa"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]
PLAYER_Y = 80
PLAYER_SIZE = LANE_WIDTH - 12
LERP_SPEED = 0.2
ENERGY_DRAIN_RATE = 4.5
ENERGY_MAX = 100
ENERGY_PER_FOOD = 40
INITIAL_FOOD = 18
AREA_ENERGY_BONUS = 15
AREA_FOOD_BONUS = 1
HORIZON_Y = 440
NIGHT_START_TIME = 55.0
NIGHT_FULL_TIME = 80.0

# Game states
STATE_INTRO = "intro"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_AREA_TRANSITION = "area_transition"


class Obstacle:
    """Base obstacle class."""

    def __init__(self, x, y, width, height, color, speed=None):
        self.sprite = arcade.SpriteSolidColor(width=width, height=height, color=color)
        self.sprite.center_x = x
        self.sprite.center_y = y
        self.speed = speed
        self.color = color
        self.width = width
        self.height = height

    def update(self, obstacle_speed):
        speed = self.speed if self.speed is not None else obstacle_speed
        self.sprite.center_y -= speed

    def draw_with_glow(self):
        arcade.draw_rect_filled(
            arcade.LRBT(
                left=self.sprite.left - 4,
                right=self.sprite.right + 4,
                bottom=self.sprite.bottom - 4,
                top=self.sprite.top + 4,
            ),
            color=(*self.color[:3], 80),
        )
        arcade.draw_sprite(self.sprite)


class TideObstacle(Obstacle):
    """Faster moving obstacle."""


class CurrentObstacle(Obstacle):
    """Traps player in specific lanes."""

    def __init__(self, x, y, width, height, color, trapped_lanes):
        super().__init__(x, y, width, height, color)
        self.trapped_lanes = trapped_lanes


class CoastguardObstacle(Obstacle):
    """Chases player if spotted."""

    def __init__(self, x, y):
        super().__init__(x, y, LANE_WIDTH - 8, 30, arcade.color.WHITE)
        self.spotted = False
        self.chase_timer = 0
        self.visibility_range = 150

    def check_spotted(self, player_x):
        distance = abs(player_x - self.sprite.center_x)
        if distance < self.visibility_range:
            self.spotted = True
            self.chase_timer = 300

    def update(self, obstacle_speed, player_x=None):
        if self.spotted and player_x is not None:
            direction = 1 if player_x > self.sprite.center_x else -1
            self.sprite.center_x += direction * 3
            self.sprite.center_y -= obstacle_speed * 0.5
            self.chase_timer -= 1

            if self.chase_timer <= 0:
                self.spotted = False
        else:
            self.sprite.center_y -= obstacle_speed


class RunnerGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        arcade.set_background_color((5, 5, 15))

        self.state = STATE_INTRO

        self.player_sprite = None
        self.obstacle_list = []
        self.particles = arcade.SpriteList()

        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]
        self.energy = ENERGY_MAX
        self.food = INITIAL_FOOD
        self.score = 0
        self.best_score = 0
        self.distance = 0

        self.game_time = 0.0
        self.spawn_timer = 0.0
        self.obstacle_speed = 7.0
        self.area = 1
        self.area_timer = 0.0
        self.area_lengths = [1500, 1800, 2000, 2200, 2500, 2800]
        self.difficulty_multiplier = 1.0

        self.intro_text = [
            "You are a sailor.",
            "Your family is waiting for you in Italy.",
            "You've been hired to guide a boat across the Mediterranean.",
            "Food and Energy are your only resources.",
            "Energy drains constantly. Food restores it.",
            "Hit obstacles to lose Energy. Lose all Energy, and the journey ends.",
            "Each level shows a different part of the crossing and what people face there.",
            "Press SPACE to continue...",
        ]
        self.intro_index = 0
        self.intro_timer = 0.0

        self.area_descriptions = [
            {
                "title": "THE DEPARTURE",
                "journey": "This is the moment of leaving. The boat is small, the supplies are limited, and the choice to cross already carries fear and hope at the same time.",
                "explanation": "People often begin by packing only what they can carry and leaving behind home, family, and certainty.",
                "focus": "Use this opening stretch to build a safe reserve of Energy and Food.",
            },
            {
                "title": "OPEN WATERS",
                "journey": "Out here, the sea feels endless. There is no shoreline to follow, only distance, fatigue, and the pressure of keeping the boat moving.",
                "explanation": "Long crossings test endurance. Every mistake costs more because help is far away.",
                "focus": "Stay steady and avoid unnecessary collisions. Conserving Energy matters most here.",
            },
            {
                "title": "THE NARROWS",
                "journey": "The route tightens and the safe path shrinks. Currents, rocks, and tight passages leave less room to recover from a bad move.",
                "explanation": "Migrants often have to navigate crowded or dangerous routes where one wrong turn can turn a delay into disaster.",
                "focus": "React early and keep your boat centered when the channel closes in.",
            },
            {
                "title": "THE WATCHLINE",
                "journey": "Now the risk is not just the sea. Patrols become part of the journey, and staying hidden can matter as much as staying afloat.",
                "explanation": "People on the move can face surveillance, interception, and the fear of being spotted when they are already exhausted.",
                "focus": "Move carefully. Avoid attention and protect the Energy you still have.",
            },
            {
                "title": "THE APPROACH",
                "journey": "This is the hardest part for many crossings. The boat is tired, the body is tired, and the final stretch still asks for more.",
                "explanation": "The last leg is where patience and rationing pay off. The journey becomes a test of discipline as much as survival.",
                "focus": "Keep your line, use Food only when you truly need it, and do not panic.",
            },
            {
                "title": "LAMPEDUSA",
                "journey": "The shore is close. Relief is mixed with uncertainty, because reaching land is only one part of the story.",
                "explanation": "Arriving can mean safety, but it can also mean more waiting, more checks, and the emotional weight of everything left behind.",
                "focus": "Hold on to the last of your Energy and bring the boat home.",
            },
        ]

        self.setup()

    def setup(self):
        """Initialize game state."""
        self.state = STATE_PLAYING
        self.obstacle_list = []
        self.particles = arcade.SpriteList()

        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]

        self.player_sprite = arcade.SpriteSolidColor(
            width=PLAYER_SIZE,
            height=PLAYER_SIZE,
            color=arcade.color.CYAN,
        )
        self.player_sprite.center_x = self.target_x
        self.player_sprite.center_y = PLAYER_Y

        self.energy = ENERGY_MAX
        self.food = INITIAL_FOOD
        self.score = 0
        self.distance = 0
        self.game_time = 0.0
        self.spawn_timer = 0.0
        self.obstacle_speed = 7.0
        self.area = 1
        self.area_timer = 0.0
        self.difficulty_multiplier = 1.0

    def spawn_wave(self):
        """Spawn obstacles based on current area."""
        if self.area == 1:
            self.spawn_basic_wave()
        elif self.area == 2:
            self.spawn_tidal_wave()
        elif self.area == 3:
            self.spawn_narrows_wave()
        elif self.area == 4:
            self.spawn_coastguard_wave()
        else:
            self.spawn_coastguard_wave()
            if random.random() < 0.4:
                self.spawn_tidal_wave()

    def spawn_basic_wave(self):
        """Spawn basic rocks."""
        num_obstacles = random.randint(1, min(4, 1 + int(self.game_time // 15)))
        lanes_to_use = random.sample(range(NUM_LANES), k=num_obstacles)

        for lane_idx in lanes_to_use:
            x = LANES[lane_idx]
            height = random.choice([20, 30, 40])
            color = random.choice(
                [
                    arcade.color.ELECTRIC_CRIMSON,
                    arcade.color.MAGENTA,
                    arcade.color.HOT_PINK,
                ]
            )
            obstacle = Obstacle(x, HEIGHT + 50, LANE_WIDTH - 4, height, color)
            self.obstacle_list.append(obstacle)

    def spawn_tidal_wave(self):
        """Spawn faster obstacles."""
        if self.area == 2:
            num_obstacles = random.randint(1, 3)
            speed_multiplier = 1.25
        else:
            num_obstacles = random.randint(2, 5)
            speed_multiplier = 1.5
        lanes_to_use = random.sample(range(NUM_LANES), k=num_obstacles)

        for lane_idx in lanes_to_use:
            x = LANES[lane_idx]
            height = random.choice([25, 35, 45])
            obstacle = TideObstacle(
                x,
                HEIGHT + 50,
                LANE_WIDTH - 4,
                height,
                arcade.color.LIGHT_BLUE,
                speed=self.obstacle_speed * speed_multiplier,
            )
            self.obstacle_list.append(obstacle)

    def spawn_narrows_wave(self):
        """Spawn obstacles near the sides as the channel narrows."""
        available_lanes = max(8, NUM_LANES - int(self.area_timer // 2))
        lane_offset = (NUM_LANES - available_lanes) // 2

        num_obstacles = random.randint(3, 6)
        valid_lanes = list(range(lane_offset)) + list(
            range(NUM_LANES - lane_offset, NUM_LANES)
        )

        if valid_lanes:
            lanes_to_use = random.sample(valid_lanes, k=min(num_obstacles, len(valid_lanes)))
            for lane_idx in lanes_to_use:
                x = LANES[lane_idx]
                obstacle = Obstacle(
                    x,
                    HEIGHT + 50,
                    LANE_WIDTH - 4,
                    random.choice([30, 40, 50]),
                    arcade.color.DARK_SLATE_GRAY,
                )
                self.obstacle_list.append(obstacle)

    def spawn_coastguard_wave(self):
        """Spawn coastguard boats or regular obstacles."""
        if random.random() < 0.3:
            x = random.choice(LANES)
            obstacle = CoastguardObstacle(x, HEIGHT + 50)
            self.obstacle_list.append(obstacle)
        else:
            self.spawn_basic_wave()

    def create_explosion(self, x, y):
        """Create particle explosion effect."""
        for _ in range(20):
            particle = arcade.SpriteSolidColor(width=6, height=6, color=arcade.color.ORANGE)
            particle.center_x = x + random.uniform(-10, 10)
            particle.center_y = y + random.uniform(-10, 10)
            particle.change_x = random.uniform(-6, 6)
            particle.change_y = random.uniform(-6, 6)
            particle.lifetime = 60
            self.particles.append(particle)

    def on_draw(self):
        """Render the game."""
        self.clear()

        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_PLAYING:
            self.draw_game()
        elif self.state == STATE_AREA_TRANSITION:
            self.draw_area_transition()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()

    def draw_game(self):
        """Draw main game screen."""
        self.draw_ocean_background()

        for obstacle in self.obstacle_list:
            obstacle.draw_with_glow()

        self.draw_boat()

        for particle in self.particles:
            arcade.draw_sprite(particle)

        bar_width = 200
        bar_height = 20
        bar_x = 20
        bar_y = HEIGHT - 35

        arcade.draw_rect_outline(
            arcade.LRBT(
                left=bar_x,
                right=bar_x + bar_width,
                bottom=bar_y,
                top=bar_y + bar_height,
            ),
            color=arcade.color.WHITE,
            border_width=2,
        )

        food_ratio = max(0, min(1, self.food / 15.0))
        if food_ratio > 0.3:
            food_color = arcade.color.GREEN
        elif food_ratio > 0.1:
            food_color = arcade.color.ORANGE
        else:
            food_color = arcade.color.RED

        arcade.draw_rect_filled(
            arcade.LRBT(
                left=bar_x,
                right=bar_x + (bar_width * food_ratio),
                bottom=bar_y,
                top=bar_y + bar_height,
            ),
            color=food_color,
        )

        arcade.draw_text(
            f"FOOD: {int(self.food)}",
            bar_x + 210,
            bar_y + 2,
            color=arcade.color.WHITE,
            font_size=14,
            bold=True,
        )

        energy_bar_y = bar_y - 22
        energy_ratio = max(0, min(1, self.energy / ENERGY_MAX))
        if energy_ratio > 0.5:
            energy_color = arcade.color.GREEN
        elif energy_ratio > 0.2:
            energy_color = arcade.color.ORANGE
        else:
            energy_color = arcade.color.RED

        arcade.draw_rect_outline(
            arcade.LRBT(
                left=bar_x,
                right=bar_x + bar_width,
                bottom=energy_bar_y,
                top=energy_bar_y + bar_height,
            ),
            color=arcade.color.WHITE,
            border_width=2,
        )
        arcade.draw_rect_filled(
            arcade.LRBT(
                left=bar_x,
                right=bar_x + (bar_width * energy_ratio),
                bottom=energy_bar_y,
                top=energy_bar_y + bar_height,
            ),
            color=energy_color,
        )
        arcade.draw_text(
            f"ENERGY: {int(self.energy)}",
            bar_x + 210,
            energy_bar_y + 2,
            color=arcade.color.WHITE,
            font_size=14,
            bold=True,
        )
        arcade.draw_text(
            f"DISTANCE: {int(self.distance)}m",
            WIDTH - 180,
            HEIGHT - 35,
            color=arcade.color.CYAN,
            font_size=14,
            bold=True,
        )
        arcade.draw_text(
            f"AREA: {self.area}/{len(self.area_descriptions)}",
            WIDTH - 180,
            HEIGHT - 55,
            color=arcade.color.LIGHT_CYAN,
            font_size=12,
        )
        arcade.draw_text(
            self.area_descriptions[self.area - 1]["title"],
            WIDTH // 2,
            HEIGHT - 28,
            color=arcade.color.WHITE,
            font_size=16,
            anchor_x="center",
            bold=True,
        )

    def draw_intro(self):
        """Draw introduction screen."""
        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=0, top=HEIGHT),
            color=(5, 5, 15),
        )

        arcade.draw_text(
            "THE JOURNEY",
            WIDTH // 2,
            HEIGHT - 80,
            color=arcade.color.CYAN,
            font_size=36,
            anchor_x="center",
            bold=True,
        )
        arcade.draw_text(
            "A Crossing to Lampedusa",
            WIDTH // 2,
            HEIGHT - 130,
            color=arcade.color.LIGHT_CYAN,
            font_size=16,
            anchor_x="center",
        )

        if self.intro_index < len(self.intro_text):
            text = self.intro_text[self.intro_index]
            arcade.draw_text(
                text,
                WIDTH // 2,
                HEIGHT // 2,
                color=arcade.color.WHITE,
                font_size=14,
                anchor_x="center",
                width=WIDTH - 100,
            )

        arcade.draw_text(
            "Press SPACE to continue",
            WIDTH // 2,
            50,
            color=arcade.color.GRAY,
            font_size=12,
            anchor_x="center",
        )

    def draw_area_transition(self):
        """Draw area transition screen."""
        self.draw_ocean_background()
        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=0, top=HEIGHT),
            color=(0, 0, 0, 120),
        )

        if self.area <= len(self.area_descriptions):
            stage = self.area_descriptions[self.area - 1]
            panel_left = WIDTH // 2 - 270
            panel_right = WIDTH // 2 + 270
            panel_bottom = HEIGHT // 2 - 145
            panel_top = HEIGHT // 2 + 120

            arcade.draw_rect_filled(
                arcade.LRBT(
                    left=panel_left,
                    right=panel_right,
                    bottom=panel_bottom,
                    top=panel_top,
                ),
                color=(10, 25, 48, 220),
            )
            arcade.draw_rect_outline(
                arcade.LRBT(
                    left=panel_left,
                    right=panel_right,
                    bottom=panel_bottom,
                    top=panel_top,
                ),
                color=(120, 200, 255),
                border_width=2,
            )

            arcade.draw_text(
                f"STAGE {self.area} OF {len(self.area_descriptions)}",
                WIDTH // 2,
                HEIGHT // 2 + 95,
                color=arcade.color.LIGHT_CYAN,
                font_size=12,
                anchor_x="center",
                bold=True,
            )
            arcade.draw_text(
                stage["title"],
                WIDTH // 2,
                HEIGHT // 2 + 65,
                color=arcade.color.CYAN,
                font_size=26,
                anchor_x="center",
                bold=True,
            )
            arcade.draw_text(
                stage["journey"],
                WIDTH // 2,
                HEIGHT // 2 + 5,
                color=arcade.color.WHITE,
                font_size=13,
                anchor_x="center",
                width=WIDTH - 100,
                multiline=True,
                align="center",
            )
            arcade.draw_text(
                "What this stage means",
                WIDTH // 2,
                HEIGHT // 2 - 70,
                color=arcade.color.LIGHT_CYAN,
                font_size=12,
                anchor_x="center",
                bold=True,
            )
            arcade.draw_text(
                stage["explanation"],
                WIDTH // 2,
                HEIGHT // 2 - 100,
                color=arcade.color.WHITE,
                font_size=12,
                anchor_x="center",
                width=WIDTH - 120,
                multiline=True,
                align="center",
            )
            arcade.draw_text(
                f"How to survive: {stage['focus']}",
                WIDTH // 2,
                HEIGHT // 2 - 135,
                color=arcade.color.LIGHT_YELLOW,
                font_size=11,
                anchor_x="center",
                width=WIDTH - 120,
                multiline=True,
                align="center",
            )

        arcade.draw_text(
            "Press SPACE to continue",
            WIDTH // 2,
            50,
            color=arcade.color.GRAY,
            font_size=12,
            anchor_x="center",
        )

    def draw_game_over(self):
        """Draw game over screen."""
        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=0, top=HEIGHT),
            color=(0, 0, 0, 180),
        )

        arcade.draw_rect_filled(
            arcade.LRBT(
                left=WIDTH // 2 - 180,
                right=WIDTH // 2 + 180,
                bottom=HEIGHT // 2 - 100,
                top=HEIGHT // 2 + 100,
            ),
            color=(20, 20, 40),
        )
        arcade.draw_rect_outline(
            arcade.LRBT(
                left=WIDTH // 2 - 180,
                right=WIDTH // 2 + 180,
                bottom=HEIGHT // 2 - 100,
                top=HEIGHT // 2 + 100,
            ),
            color=arcade.color.RED,
            border_width=3,
        )

        arcade.draw_text(
            "JOURNEY ENDED",
            WIDTH // 2,
            HEIGHT // 2 + 60,
            color=arcade.color.RED,
            font_size=24,
            anchor_x="center",
            bold=True,
        )
        arcade.draw_text(
            f"Distance Traveled: {int(self.distance)}m",
            WIDTH // 2,
            HEIGHT // 2 + 20,
            color=arcade.color.WHITE,
            font_size=14,
            anchor_x="center",
        )
        arcade.draw_text(
            f"Best Distance: {int(self.best_score)}m",
            WIDTH // 2,
            HEIGHT // 2 - 10,
            color=arcade.color.LIGHT_CYAN,
            font_size=12,
            anchor_x="center",
        )
        arcade.draw_text(
            "Press R to Try Again",
            WIDTH // 2,
            HEIGHT // 2 - 60,
            color=arcade.color.CYAN,
            font_size=14,
            anchor_x="center",
        )

    def get_night_factor(self):
        """Return a 0-1 blend value for the day-to-night transition."""
        return max(
            0.0,
            min(1.0, (self.game_time - NIGHT_START_TIME) / (NIGHT_FULL_TIME - NIGHT_START_TIME)),
        )

    def blend_color(self, start_color, end_color, t):
        """Blend two RGB colors."""
        return (
            int(start_color[0] * (1 - t) + end_color[0] * t),
            int(start_color[1] * (1 - t) + end_color[1] * t),
            int(start_color[2] * (1 - t) + end_color[2] * t),
        )

    def draw_ocean_background(self):
        """Draw a layered sea and sky backdrop."""
        night = self.get_night_factor()
        sky_top = self.blend_color((166, 214, 255), (14, 24, 64), night)
        sky_bottom = self.blend_color((211, 236, 255), (5, 10, 24), night)
        ocean_top = self.blend_color((43, 119, 171), (6, 18, 46), night)
        ocean_bottom = self.blend_color((6, 42, 90), (1, 6, 22), night)

        sky_height = HEIGHT - HORIZON_Y
        for i in range(sky_height):
            t = i / max(1, sky_height - 1)
            color = (
                int(sky_top[0] * (1 - t) + sky_bottom[0] * t),
                int(sky_top[1] * (1 - t) + sky_bottom[1] * t),
                int(sky_top[2] * (1 - t) + sky_bottom[2] * t),
            )
            arcade.draw_rect_filled(
                arcade.LRBT(left=0, right=WIDTH, bottom=HORIZON_Y + i, top=HORIZON_Y + i + 1),
                color=color,
            )

        ocean_height = HORIZON_Y
        for i in range(ocean_height):
            t = i / max(1, ocean_height - 1)
            color = (
                int(ocean_top[0] * (1 - t) + ocean_bottom[0] * t),
                int(ocean_top[1] * (1 - t) + ocean_bottom[1] * t),
                int(ocean_top[2] * (1 - t) + ocean_bottom[2] * t),
            )
            arcade.draw_rect_filled(
                arcade.LRBT(left=0, right=WIDTH, bottom=i, top=i + 1),
                color=color,
            )

        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=HORIZON_Y - 2, top=HORIZON_Y + 6),
            color=(255, 255, 255, int(18 * (1 - night) + 6 * night)),
        )

        sun_x = WIDTH - 110
        sun_y = HEIGHT - 100
        if night < 0.6:
            sun_alpha = int(180 * (1 - night * 1.3))
            core_alpha = int(220 * (1 - night * 1.3))
            arcade.draw_circle_filled(sun_x, sun_y, 34, (255, 240, 190, max(0, sun_alpha)))
            arcade.draw_circle_filled(sun_x, sun_y, 22, (255, 228, 153, max(0, core_alpha)))
        else:
            moon_alpha = int(200 * min(1.0, (night - 0.5) * 2))
            arcade.draw_circle_filled(sun_x, sun_y, 28, (230, 240, 255, moon_alpha))
            arcade.draw_circle_filled(sun_x - 6, sun_y + 2, 24, (255, 255, 255, 0))

        if night > 0.15:
            star_alpha = int(160 * min(1.0, (night - 0.15) / 0.85))
            star_positions = [
                (70, 520), (145, 560), (240, 505), (320, 540), (430, 565),
                (530, 515), (610, 550), (710, 530), (860, 555), (950, 510),
            ]
            for sx, sy in star_positions:
                arcade.draw_circle_filled(sx, sy, 2, (255, 255, 255, star_alpha))
                arcade.draw_circle_filled(sx, sy, 1, (255, 255, 255, min(255, star_alpha + 30)))

        wave_base = self.game_time * 3.5
        for row in range(10):
            y = 35 + row * 32
            offset = math.sin((wave_base + row) * 0.8) * 10
            wave_color = self.blend_color((160, 230, 255), (95, 160, 220), night)
            wave_alpha = int((28 if row % 2 == 0 else 18) * (1 - night) + (42 if row % 2 == 0 else 28) * night)
            for x in range(-40, WIDTH + 40, 80):
                arcade.draw_arc_outline(
                    x + offset,
                    y,
                    60,
                    12,
                    (*wave_color, wave_alpha),
                    0,
                    180,
                    3,
                )

        for x in range(0, WIDTH + 1, LANE_WIDTH):
            arcade.draw_line(
                start_x=x,
                start_y=0,
                end_x=x,
                end_y=HEIGHT,
                color=(180, 220, 255, int(14 * (1 - night) + 8 * night)),
                line_width=1,
            )

    def draw_boat(self):
        """Draw the player as a small boat."""
        x = self.player_sprite.center_x
        y = self.player_sprite.center_y

        arcade.draw_ellipse_filled(x + 2, y - 10, 34, 10, (0, 0, 0, 70))
        arcade.draw_polygon_filled(
            [
                (x - 18, y - 8),
                (x + 18, y - 8),
                (x + 12, y - 18),
                (x - 12, y - 18),
            ],
            (108, 62, 30),
        )
        arcade.draw_polygon_filled(
            [
                (x - 16, y - 7),
                (x + 16, y - 7),
                (x + 10, y - 15),
                (x - 10, y - 15),
            ],
            (165, 96, 52),
        )
        arcade.draw_rect_filled(
            arcade.LRBT(left=x - 7, right=x + 7, bottom=y - 4, top=y + 7),
            color=(230, 235, 240),
        )
        arcade.draw_triangle_filled(
            x - 2,
            y + 17,
            x - 2,
            y - 2,
            x + 17,
            y + 6,
            (245, 248, 255),
        )
        arcade.draw_triangle_filled(
            x - 2,
            y + 15,
            x - 2,
            y + 1,
            x - 18,
            y + 7,
            (210, 220, 230),
        )
        arcade.draw_line(x - 2, y + 17, x - 2, y - 14, (80, 50, 30), 2)
        arcade.draw_line(x - 16, y - 10, x + 16, y - 10, (255, 255, 255, 80), 2)
        arcade.draw_circle_filled(x, y - 2, 3, (255, 255, 255))

    def on_update(self, delta_time):
        """Update game logic."""
        if self.state == STATE_INTRO:
            self.intro_timer += delta_time
        elif self.state == STATE_AREA_TRANSITION:
            pass
        elif self.state == STATE_PLAYING:
            self.update_game(delta_time)
        elif self.state == STATE_GAME_OVER:
            self.update_particles()

    def update_game(self, delta_time):
        """Update main game state."""
        self.game_time += delta_time
        self.distance += delta_time * 50
        self.area_timer += delta_time
        self.energy -= ENERGY_DRAIN_RATE * delta_time

        if self.area < len(self.area_descriptions) and self.area_timer > 30:
            self.area += 1
            self.area_timer = 0
            self.energy = min(ENERGY_MAX, self.energy + AREA_ENERGY_BONUS)
            self.food += AREA_FOOD_BONUS
            self.state = STATE_AREA_TRANSITION
            return

        self.player_sprite.center_x += (
            self.target_x - self.player_sprite.center_x
        ) * LERP_SPEED

        self.obstacle_speed = 6.5 + (self.game_time * 0.22) + (self.area * 0.4)
        if self.area == 2:
            self.obstacle_speed -= 0.5

        spawn_rate = max(0.22, 0.7 - (self.game_time * 0.01))
        self.spawn_timer += delta_time
        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0.0
            self.spawn_wave()

        for obstacle in self.obstacle_list[:]:
            if isinstance(obstacle, CoastguardObstacle):
                obstacle.update(self.obstacle_speed, self.player_sprite.center_x)
                obstacle.check_spotted(self.player_sprite.center_x)
            else:
                obstacle.update(self.obstacle_speed)

            if obstacle.sprite.top < 0:
                self.obstacle_list.remove(obstacle)

        for obstacle in self.obstacle_list[:]:
            if arcade.check_for_collision(self.player_sprite, obstacle.sprite):
                if isinstance(obstacle, CoastguardObstacle) and obstacle.spotted:
                    self.game_over_event()
                else:
                    self.energy -= 20
                    self.create_explosion(
                        self.player_sprite.center_x,
                        self.player_sprite.center_y,
                    )
                    self.obstacle_list.remove(obstacle)

        self.update_particles()

        if self.energy <= 0:
            self.game_over_event()

    def update_particles(self):
        """Update particle effects."""
        for particle in self.particles[:]:
            particle.center_x += particle.change_x
            particle.center_y += particle.change_y
            particle.change_y -= 0.2
            particle.lifetime -= 1

            green = max(0, min(255, int(255 * (particle.lifetime / 60))))
            particle.color = (255, green, 0)

            if particle.lifetime <= 0:
                self.particles.remove(particle)

    def game_over_event(self):
        """Handle game over."""
        self.state = STATE_GAME_OVER
        self.best_score = max(self.best_score, self.distance)

        if self.energy > 0:
            self.create_explosion(
                self.player_sprite.center_x,
                self.player_sprite.center_y,
            )

    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if self.state == STATE_INTRO:
            if key == arcade.key.SPACE:
                self.intro_index += 1
                if self.intro_index >= len(self.intro_text):
                    self.setup()

        elif self.state == STATE_AREA_TRANSITION:
            if key == arcade.key.SPACE:
                self.state = STATE_PLAYING

        elif self.state == STATE_PLAYING:
            if key in (arcade.key.LEFT, arcade.key.A) and self.player_lane > 0:
                self.player_lane -= 1
                self.target_x = LANES[self.player_lane]

            elif key in (arcade.key.RIGHT, arcade.key.D) and self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.target_x = LANES[self.player_lane]

            if key == arcade.key.SPACE and self.food > 0:
                self.energy = min(ENERGY_MAX, self.energy + ENERGY_PER_FOOD)
                self.food -= 1

        elif self.state == STATE_GAME_OVER:
            if key == arcade.key.R:
                self.state = STATE_INTRO
                self.intro_index = 0


def main():
    RunnerGame()
    arcade.run()


if __name__ == "__main__":
    main()
