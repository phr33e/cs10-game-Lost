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
SLOW_LERP_SPEED = 0.12
ENERGY_MAX = 100
ENERGY_PER_FOOD = 28
INITIAL_FOOD = 11
AREA_ENERGY_BONUS = 5
AREA_FOOD_BONUS = 1
HORIZON_Y = 440
NIGHT_START_TIME = 55.0
NIGHT_FULL_TIME = 80.0
FREE_MOVE_SPEED = 160
FREE_MOVE_SLOW_SPEED = 120
PLAYER_MIN_Y = 55
PLAYER_MAX_Y = 205
ENERGY_DRAIN_MIN_SECONDS = 50.0
ENERGY_DRAIN_MAX_SECONDS = 105.0
BASE_OBSTACLE_SPEED = 5.4
OBSTACLE_SPEED_RAMP = 0.18
BASE_SPAWN_INTERVAL = 0.92
MIN_SPAWN_INTERVAL = 0.5
LOW_ENERGY_THRESHOLD = 0.35
LOW_ENERGY_FULL_DARK = 0.08

# Game states
STATE_INTRO = "intro"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_AREA_TRANSITION = "area_transition"
MIGRANT_DIALOGUE_KEY = arcade.key.T


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
        self.render_mode = "rock"

    def update(self, obstacle_speed):
        speed = self.speed if self.speed is not None else obstacle_speed
        self.sprite.center_y -= speed

    def project_point(self, x, y):
        """Project world coordinates into the forward-looking view."""
        max_y = HEIGHT + 60
        travel = max(0.0, min(1.0, (y - PLAYER_Y) / max(1.0, max_y - PLAYER_Y)))
        depth_scale = 0.28 + 0.72 * (1.0 - travel)
        projected_x = (WIDTH / 2) + ((x - (WIDTH / 2)) * depth_scale)
        projected_y = PLAYER_Y + ((HORIZON_Y - PLAYER_Y) * (travel ** 1.25))
        return projected_x, projected_y, depth_scale

    def draw_with_glow(self):
        screen_x, screen_y, scale = self.project_point(self.sprite.center_x, self.sprite.center_y)
        screen_width = max(10, self.sprite.width * scale)
        screen_height = max(10, self.sprite.height * scale)
        arcade.draw_rect_filled(
            arcade.LRBT(
                left=screen_x - screen_width * 0.6,
                right=screen_x + screen_width * 0.6,
                bottom=screen_y - screen_height * 0.6,
                top=screen_y + screen_height * 0.6,
            ),
            color=(*self.color[:3], 80),
        )
        if self.render_mode == "rock":
            self.draw_rock(screen_x, screen_y, screen_width, screen_height)
        else:
            arcade.draw_rect_filled(
                arcade.LRBT(
                    left=screen_x - screen_width * 0.35,
                    right=screen_x + screen_width * 0.35,
                    bottom=screen_y - screen_height * 0.55,
                    top=screen_y + screen_height * 0.55,
                ),
                color=self.color,
            )
            arcade.draw_rect_outline(
                arcade.LRBT(
                    left=screen_x - screen_width * 0.35,
                    right=screen_x + screen_width * 0.35,
                    bottom=screen_y - screen_height * 0.55,
                    top=screen_y + screen_height * 0.55,
                ),
                color=(255, 255, 255, 75),
                border_width=1,
            )

    def draw_rock(self, x, y, width, height):
        """Draw a rounded rock-like obstacle."""
        base_color = self.color
        shadow_color = (
            max(0, base_color[0] - 35),
            max(0, base_color[1] - 35),
            max(0, base_color[2] - 35),
        )
        highlight_color = (
            min(255, base_color[0] + 25),
            min(255, base_color[1] + 25),
            min(255, base_color[2] + 25),
        )

        rock_points = [
            (x - width * 0.25, y - height * 0.15),
            (x - width * 0.14, y + height * 0.38),
            (x, y + height * 0.52),
            (x + width * 0.2, y + height * 0.26),
            (x + width * 0.26, y - height * 0.08),
            (x + width * 0.06, y - height * 0.5),
            (x - width * 0.12, y - height * 0.42),
        ]

        arcade.draw_ellipse_filled(x, y - 3, width * 1.05, height * 0.95, shadow_color)
        arcade.draw_polygon_filled(rock_points, base_color)
        arcade.draw_polygon_filled(
            [
                (x - width * 0.22, y + height * 0.18),
                (x - width * 0.02, y + height * 0.34),
                (x + width * 0.18, y + height * 0.16),
                (x + width * 0.03, y - height * 0.02),
            ],
            highlight_color,
        )
        arcade.draw_line(
            x - width * 0.2,
            y - height * 0.1,
            x + width * 0.18,
            y + height * 0.08,
            (255, 255, 255, 40),
            2,
        )


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
        self.render_mode = "coastguard"
        self.spotted = False
        self.chase_timer = 0
        self.visibility_range = 150

    def check_spotted(self, player_x):
        distance = abs(player_x - self.sprite.center_x)
        if distance < self.visibility_range:
            self.spotted = True
            self.chase_timer = 480

    def update(self, obstacle_speed, player_x=None):
        if self.spotted and player_x is not None:
            direction = 1 if player_x > self.sprite.center_x else -1
            self.sprite.center_x += direction * 5
            self.sprite.center_y -= obstacle_speed * 0.8
            self.chase_timer -= 1

            if self.chase_timer <= 0:
                self.spotted = False
        else:
            self.sprite.center_y -= obstacle_speed


class FoodPickup:
    """Collectible food supply."""

    def __init__(self, x, y):
        self.sprite = arcade.SpriteSolidColor(width=22, height=22, color=(198, 126, 62))
        self.sprite.center_x = x
        self.sprite.center_y = y
        self.pulse = random.uniform(0, math.pi * 2)

    def update(self, obstacle_speed):
        self.sprite.center_y -= obstacle_speed
        self.pulse += 0.12

    def draw_with_glow(self):
        glow_alpha = int(60 + 20 * (0.5 + 0.5 * math.sin(self.pulse)))
        arcade.draw_circle_filled(
            self.sprite.center_x,
            self.sprite.center_y,
            18,
            (255, 190, 120, glow_alpha),
        )
        arcade.draw_circle_filled(
            self.sprite.center_x,
            self.sprite.center_y,
            12,
            (232, 156, 84, 220),
        )
        self.draw_food()

    def draw_food(self):
        """Draw a simple ration-box icon."""
        x = self.sprite.center_x
        y = self.sprite.center_y
        box = [
            (x - 7, y - 7),
            (x + 7, y - 7),
            (x + 9, y + 5),
            (x - 5, y + 9),
        ]
        arcade.draw_polygon_filled(box, (120, 72, 34))
        arcade.draw_rect_filled(
            arcade.LRBT(left=x - 5, right=x + 5, bottom=y - 4, top=y + 2),
            color=(255, 220, 150),
        )
        arcade.draw_line(x - 6, y + 4, x + 7, y + 4, (255, 255, 255, 120), 1)


class RunnerGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        arcade.set_background_color((5, 5, 15))

        self.state = STATE_INTRO

        self.player_sprite = None
        self.obstacle_list = []
        self.food_pickups = []
        self.particles = arcade.SpriteList()
        self.keys_down = set()
        self.food_use_cooldown = 0.0
        self.dialogue_open = False
        self.dialogue_mode = None
        self.manual_dialogue_index = 0
        self.auto_dialogue_index = 0
        self.dialogue_line_index = 0
        self.dialogue_cooldown = 0.0
        self.dialogue_line_timer = 0.0
        self.active_dialogue = None

        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]
        self.target_y = PLAYER_Y
        self.control_mode = "lane"
        self.player_move_speed = FREE_MOVE_SPEED
        self.lane_lerp_speed = LERP_SPEED
        self.energy = ENERGY_MAX
        self.energy_drain_duration = random.uniform(
            ENERGY_DRAIN_MIN_SECONDS, ENERGY_DRAIN_MAX_SECONDS
        )
        self.energy_drain_rate = ENERGY_MAX / self.energy_drain_duration
        self.food = INITIAL_FOOD
        self.score = 0
        self.best_score = 0
        self.distance = 0

        self.game_time = 0.0
        self.spawn_timer = 0.0
        self.obstacle_speed = BASE_OBSTACLE_SPEED
        self.area = 1
        self.area_timer = 0.0
        self.area_lengths = [1500, 1800, 2000, 2200, 2500, 2800]
        self.difficulty_multiplier = 1.0
        self.food_use_cooldown = 0.0

        self.intro_text = [
            "You are on a small boat carrying migrants across the Mediterranean.",
            "They are exhausted, scared, and hoping to reach safety in Italy.",
            "Listen to their stories as the journey unfolds.",
            "Food is your visible resource.",
            "A hidden stamina pool drains over time. Food restores it.",
            "Hit obstacles and your hidden stamina drops. Let it reach zero and the journey ends.",
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
                "focus": "Use this opening stretch to build a safe reserve of Food and supplies.",
            },
            {
                "title": "OPEN WATERS",
                "journey": "Out here, the sea feels endless. There is no shoreline to follow, only distance, fatigue, and the pressure of keeping the boat moving.",
                "explanation": "Long crossings test endurance. Every mistake costs more because help is far away.",
                "focus": "Stay steady and avoid unnecessary collisions. Conserving supplies matters most here.",
            },
            {
                "title": "THE NARROWS",
                "journey": "The route tightens and the safe path shrinks. Currents, rocks, and tight passages leave less room to recover from a bad move.",
                "explanation": "Migrants often have to navigate crowded or dangerous routes where one wrong turn can turn a delay into disaster.",
                "focus": "React early and keep your boat centered when the channel closes in.",
                "speed_scale": 0.75,
            },
            {
                "title": "THE WATCHLINE",
                "journey": "Now the risk is not just the sea. Patrols become part of the journey, and staying hidden can matter as much as staying afloat.",
                "explanation": "People on the move can face surveillance, interception, and the fear of being spotted when they are already exhausted.",
                "focus": "Move carefully. Avoid attention and protect the supplies you still have.",
                "movement": "free",
                "boat_speed": 135,
                "speed_scale": 0.9,
            },
            {
                "title": "THE APPROACH",
                "journey": "This is the hardest part for many crossings. The boat is tired, the body is tired, and the final stretch still asks for more.",
                "explanation": "The last leg is where patience and rationing pay off. The journey becomes a test of discipline as much as survival.",
                "focus": "Keep your line, use Food only when you truly need it, and do not panic.",
                "movement": "free",
                "boat_speed": 120,
                "speed_scale": 0.85,
            },
            {
                "title": "LAMPEDUSA",
                "journey": "The shore is close. Relief is mixed with uncertainty, because reaching land is only one part of the story.",
                "explanation": "Arriving can mean safety, but it can also mean more waiting, more checks, and the emotional weight of everything left behind.",
                "focus": "Hold on to the last of your supplies and bring the boat home.",
                "movement": "free",
                "boat_speed": 108,
                "speed_scale": 0.8,
            },
        ]
        self.migrant_dialogues = [
            {
                "manual": [
                    {
                        "speaker": "Amina",
                        "trigger_distance": 70,
                        "lines": [
                            "We left because staying meant waiting for violence to come back.",
                            "I carried only my documents and a photo of my children.",
                            "I keep telling myself this boat is the price of a safer morning.",
                        ],
                    },
                    {
                        "speaker": "Khalid",
                        "trigger_distance": 180,
                        "lines": [
                            "Before the sea, there were months of planning and fear.",
                            "You do not cross like this unless home has already stopped feeling safe.",
                        ],
                    },
                ],
                "auto": [
                    {
                        "speaker": "Youssef",
                        "trigger_distance": 130,
                        "lines": [
                            "The journey starts long before the sea. It starts when there is no work, no safety, and no way forward at home.",
                            "We crossed borders on foot before we ever saw water.",
                        ],
                    },
                    {
                        "speaker": "Mina",
                        "trigger_distance": 255,
                        "lines": [
                            "Everybody on this boat has left something behind.",
                            "Even the ones who look calm are carrying whole lives in their heads.",
                        ],
                    },
                ],
            },
            {
                "manual": [
                    {
                        "speaker": "Nadia",
                        "trigger_distance": 80,
                        "lines": [
                            "The sea makes every hour feel heavier.",
                            "We drink slowly because every sip matters and nobody knows how long this will last.",
                            "People get quiet when the waves rise, not because we do not care, but because we are trying to stay calm.",
                        ],
                    },
                    {
                        "speaker": "Hassan",
                        "trigger_distance": 190,
                        "lines": [
                            "People think the sea is the danger, but hunger and exhaustion travel with us too.",
                            "You feel both at once, and neither one is easy to ignore.",
                        ],
                    },
                ],
                "auto": [
                    {
                        "speaker": "Salim",
                        "trigger_distance": 140,
                        "lines": [
                            "Some of us are sick, some are praying, and some are just staring at the horizon.",
                            "It is strange how far hope can carry you when fear is still with you.",
                        ],
                    },
                    {
                        "speaker": "Mariam",
                        "trigger_distance": 250,
                        "lines": [
                            "When the boat rocks, everyone starts holding their breath at the same time.",
                            "You can almost hear people counting the minutes in their heads.",
                        ],
                    },
                ],
            },
            {
                "manual": [
                    {
                        "speaker": "Mariam",
                        "trigger_distance": 75,
                        "lines": [
                            "The route changes because the safest path is never really safe.",
                            "People pay what they have to strangers who promise a crossing and leave us with uncertainty instead.",
                            "One crowded boat can turn a desperate plan into a disaster in minutes.",
                        ],
                    },
                    {
                        "speaker": "Farid",
                        "trigger_distance": 170,
                        "lines": [
                            "If we had other choices, we would not be here.",
                            "The sea is the last place people go when every other door has closed.",
                        ],
                    },
                ],
                "auto": [
                    {
                        "speaker": "Ibrahim",
                        "trigger_distance": 135,
                        "lines": [
                            "We are not choosing danger because we want adventure.",
                            "We are choosing it because the alternatives were worse than the sea.",
                        ],
                    },
                    {
                        "speaker": "Leila",
                        "trigger_distance": 245,
                        "lines": [
                            "The boat feels smaller when everyone starts talking about what could go wrong.",
                            "Still, staying quiet can feel even scarier.",
                        ],
                    },
                ],
            },
            {
                "manual": [
                    {
                        "speaker": "Leila",
                        "trigger_distance": 70,
                        "lines": [
                            "When lights appear, everyone freezes.",
                            "Being seen can mean being intercepted, turned back, or losing the chance we fought for.",
                            "Even silence feels loud when you know someone is watching.",
                        ],
                    },
                    {
                        "speaker": "Omar",
                        "trigger_distance": 165,
                        "lines": [
                            "We watch the shore and the sky at the same time now.",
                            "Hope and fear both get sharper when land is near.",
                        ],
                    },
                ],
                "auto": [
                    {
                        "speaker": "Farid",
                        "trigger_distance": 130,
                        "lines": [
                            "We are tired of hiding, but we learned very quickly that fear can follow you out here too.",
                            "All we want is a place where our names do not have to be whispered.",
                        ],
                    },
                    {
                        "speaker": "Nadia",
                        "trigger_distance": 240,
                        "lines": [
                            "Every shadow can look like danger when you have spent too long running.",
                            "Even the quiet sounds different out here.",
                        ],
                    },
                ],
            },
            {
                "manual": [
                    {
                        "speaker": "Amina",
                        "trigger_distance": 70,
                        "lines": [
                            "The hardest part is that land can be close and still feel far away.",
                            "Everybody on this boat is thinking about different things: family, papers, food, and whether tomorrow is finally going to be different.",
                            "We have been holding ourselves together for so long that even relief feels complicated.",
                        ],
                    },
                    {
                        "speaker": "Rami",
                        "trigger_distance": 155,
                        "lines": [
                            "Getting close does not make the fear disappear.",
                            "It just changes what the fear is about.",
                        ],
                    },
                ],
                "auto": [
                    {
                        "speaker": "Youssef",
                        "trigger_distance": 120,
                        "lines": [
                            "We are counting every minute now.",
                            "Not because the journey is over, but because it has changed us and we need to believe the next part can be gentler.",
                        ],
                    },
                    {
                        "speaker": "Mina",
                        "trigger_distance": 230,
                        "lines": [
                            "No one stops being tired just because the shore is there.",
                            "But everybody starts hoping a little harder.",
                        ],
                    },
                ],
            },
            {
                "manual": [
                    {
                        "speaker": "Nadia",
                        "trigger_distance": 60,
                        "lines": [
                            "Reaching shore does not erase what happened on the way here.",
                            "Some of us will ask for asylum, some will call family, and some will just stand still because the body needs time to understand safety again.",
                            "The sea stays inside you for a while.",
                        ],
                    },
                    {
                        "speaker": "Salim",
                        "trigger_distance": 140,
                        "lines": [
                            "When this ends, the story does not end with it.",
                            "What happens next is another kind of crossing.",
                        ],
                    },
                ],
                "auto": [
                    {
                        "speaker": "Mariam",
                        "trigger_distance": 110,
                        "lines": [
                            "We made it this far by carrying one another.",
                            "That is the story I want people to remember: not only the crossing, but the reason we kept going.",
                        ],
                    },
                    {
                        "speaker": "Amina",
                        "trigger_distance": 225,
                        "lines": [
                            "Even after land, everybody is still listening for the sea inside their own chest.",
                            "Some feelings take longer to arrive than the boat does.",
                        ],
                    },
                ],
            },
        ]

        self.setup()

    def setup(self):
        """Initialize game state."""
        self.state = STATE_PLAYING
        self.obstacle_list = []
        self.food_pickups = []
        self.particles = arcade.SpriteList()
        self.keys_down = set()

        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]
        self.target_y = PLAYER_Y
        self.refresh_control_mode()

        self.player_sprite = arcade.SpriteSolidColor(
            width=PLAYER_SIZE,
            height=PLAYER_SIZE,
            color=arcade.color.CYAN,
        )
        self.player_sprite.center_x = self.target_x
        self.player_sprite.center_y = PLAYER_Y

        self.energy = ENERGY_MAX
        self.energy_drain_duration = random.uniform(
            ENERGY_DRAIN_MIN_SECONDS, ENERGY_DRAIN_MAX_SECONDS
        )
        self.energy_drain_rate = ENERGY_MAX / self.energy_drain_duration
        self.food = INITIAL_FOOD
        self.score = 0
        self.distance = 0
        self.game_time = 0.0
        self.spawn_timer = 0.0
        self.obstacle_speed = BASE_OBSTACLE_SPEED
        self.area = 1
        self.area_timer = 0.0
        self.difficulty_multiplier = 1.0
        self.dialogue_open = False
        self.dialogue_mode = None
        self.manual_dialogue_index = 0
        self.auto_dialogue_index = 0
        self.dialogue_line_index = 0
        self.dialogue_cooldown = 0.0
        self.dialogue_line_timer = 0.0
        self.active_dialogue = None

    def refresh_control_mode(self):
        """Set player control style based on the current area."""
        stage_index = min(self.area - 1, len(self.area_descriptions) - 1)
        stage = self.area_descriptions[stage_index]
        movement = stage.get("movement", "lane")
        speed_scale = stage.get("speed_scale", 1.0)

        self.keys_down.clear()

        if movement == "free":
            self.control_mode = "free"
            self.player_move_speed = stage.get("boat_speed", FREE_MOVE_SPEED) * speed_scale
            self.lane_lerp_speed = LERP_SPEED * speed_scale
            self.target_y = max(PLAYER_MIN_Y, min(self.target_y or PLAYER_Y, PLAYER_MAX_Y))
        else:
            self.control_mode = "lane"
            self.player_move_speed = FREE_MOVE_SPEED
            self.lane_lerp_speed = SLOW_LERP_SPEED if speed_scale < 1.0 else LERP_SPEED
            self.target_y = PLAYER_Y

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

        pickup_chance = 0.04
        if self.area == 2:
            pickup_chance = 0.07
        elif self.area >= 4:
            pickup_chance = 0.05

        if random.random() < pickup_chance:
            self.spawn_food_pickup()

    def spawn_basic_wave(self):
        """Spawn basic rocks."""
        num_obstacles = random.randint(1, min(4, 1 + int(self.game_time // 10)))
        lanes_to_use = random.sample(range(NUM_LANES), k=num_obstacles)

        for lane_idx in lanes_to_use:
            x = LANES[lane_idx]
            height = random.choice([20, 30, 40])
            color = random.choice(
                [
                    (88, 92, 100),
                    (104, 108, 116),
                    (124, 128, 136),
                ]
            )
            obstacle = Obstacle(x, HEIGHT + 50, LANE_WIDTH - 4, height, color)
            self.obstacle_list.append(obstacle)

    def spawn_tidal_wave(self):
        """Spawn faster obstacles."""
        if self.area == 2:
            num_obstacles = random.randint(1, 2)
            speed_multiplier = 1.22
        else:
            num_obstacles = random.randint(2, 4)
            speed_multiplier = 1.34
        lanes_to_use = random.sample(range(NUM_LANES), k=num_obstacles)

        for lane_idx in lanes_to_use:
            x = LANES[lane_idx]
            height = random.choice([25, 35, 45])
            color = random.choice(
                [
                    (96, 100, 108),
                    (78, 84, 92),
                    (116, 120, 128),
                ]
            )
            obstacle = TideObstacle(
                x,
                HEIGHT + 50,
                LANE_WIDTH - 4,
                height,
                color,
                speed=self.obstacle_speed * speed_multiplier,
            )
            self.obstacle_list.append(obstacle)

    def spawn_narrows_wave(self):
        """Spawn obstacles near the sides as the channel narrows."""
        available_lanes = max(8, NUM_LANES - int(self.area_timer // 2))
        lane_offset = (NUM_LANES - available_lanes) // 2

        num_obstacles = random.randint(5, 6)
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
                    (92, 96, 102),
                )
                self.obstacle_list.append(obstacle)

    def spawn_coastguard_wave(self):
        """Spawn coastguard boats or regular obstacles."""
        if random.random() < 0.58:
            x = random.choice(LANES)
            obstacle = CoastguardObstacle(x, HEIGHT + 50)
            self.obstacle_list.append(obstacle)
        else:
            self.spawn_basic_wave()

    def spawn_food_pickup(self):
        """Spawn a food pickup that restores food supplies."""
        x = random.choice(LANES)
        pickup = FoodPickup(x, HEIGHT + 50)
        self.food_pickups.append(pickup)

    def recycle_obstacle(self, obstacle):
        """Loop a rock-style obstacle back to the top so it keeps moving."""
        obstacle.sprite.center_y = HEIGHT + 50
        if isinstance(obstacle, CoastguardObstacle):
            obstacle.spotted = False
            obstacle.chase_timer = 0
            obstacle.sprite.center_x = random.choice(LANES)

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

    def create_food_burst(self, x, y):
        """Create a bright burst for food pickup feedback."""
        for _ in range(14):
            particle = arcade.SpriteSolidColor(width=4, height=4, color=(255, 210, 120))
            particle.center_x = x + random.uniform(-8, 8)
            particle.center_y = y + random.uniform(-8, 8)
            particle.change_x = random.uniform(-4, 4)
            particle.change_y = random.uniform(-4, 4)
            particle.lifetime = 40
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

        for pickup in self.food_pickups:
            pickup.draw_with_glow()

        self.draw_boat()

        self.draw_energy_drain_overlay()
        self.draw_migrant_dialogue()

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
        supply_ratio = max(0, min(1, self.energy / ENERGY_MAX))
        if supply_ratio > 0.45:
            supply_text = "SUPPLIES STABLE"
        elif supply_ratio > 0.2:
            supply_text = "SUPPLIES RUNNING LOW"
        else:
            supply_text = "SUPPLIES CRITICAL"
        arcade.draw_text(
            supply_text,
            WIDTH // 2,
            HEIGHT - 48,
            color=arcade.color.LIGHT_YELLOW,
            font_size=11,
            anchor_x="center",
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
        if self.control_mode == "free":
            control_text = f"WASD: free steering | Speed: {int(self.player_move_speed)}"
        else:
            control_text = "A/D: steer between lanes | SPACE: use food"
        arcade.draw_text(
            control_text,
            WIDTH // 2,
            HEIGHT - 68,
            color=arcade.color.LIGHT_YELLOW,
            font_size=10,
            anchor_x="center",
        )
        if self.manual_dialogue_available() and not self.dialogue_open:
            dialogue_hint = "Press T to talk to the passengers"
            arcade.draw_text(
                dialogue_hint,
                WIDTH // 2,
                20,
                color=arcade.color.LIGHT_GRAY,
                font_size=10,
                anchor_x="center",
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
            if stage.get("movement") == "free":
                controls = f"This stage opens up: use WASD to move freely. Boat speed: {stage.get('boat_speed', FREE_MOVE_SPEED)}"
            else:
                controls = "This stage keeps lane steering. Use A/D to shift left or right."
            arcade.draw_text(
                controls,
                WIDTH // 2,
                HEIGHT // 2 - 158,
                color=arcade.color.CYAN,
                font_size=10,
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

    def draw_migrant_dialogue(self):
        """Draw the current migrant conversation as a boat-side overlay."""
        if not self.dialogue_open and self.active_dialogue is None:
            return

        is_auto = self.dialogue_mode == "auto"
        panel_left = 40
        panel_right = WIDTH - 40
        panel_bottom = 40
        panel_top = 165 if not is_auto else 145
        panel_color = (10, 18, 30, 220) if not is_auto else (38, 24, 10, 210)
        panel_outline = (132, 202, 255) if not is_auto else (255, 196, 120)

        arcade.draw_rect_filled(
            arcade.LRBT(left=panel_left, right=panel_right, bottom=panel_bottom, top=panel_top),
            color=panel_color,
        )
        arcade.draw_rect_outline(
            arcade.LRBT(left=panel_left, right=panel_right, bottom=panel_bottom, top=panel_top),
            color=panel_outline,
            border_width=2,
        )

        if self.active_dialogue is None:
            label = "Passengers start talking over the engine" if is_auto else "A passenger leans toward you"
            footer = "While you steer" if is_auto else "Press T to listen"
            arcade.draw_text(
                label,
                panel_left + 18,
                panel_top - 32,
                color=arcade.color.LIGHT_YELLOW if is_auto else arcade.color.LIGHT_CYAN,
                font_size=13,
                bold=True,
            )
            arcade.draw_text(
                footer,
                panel_left + 18,
                panel_bottom + 18,
                color=arcade.color.WHITE,
                font_size=11,
            )
            return

        speaker = self.active_dialogue["speaker"]
        line = self.active_dialogue["lines"][self.dialogue_line_index]

        arcade.draw_text(
            f"{speaker} says:",
            panel_left + 18,
            panel_top - 32,
            color=arcade.color.LIGHT_CYAN,
            font_size=13,
            bold=True,
        )
        arcade.draw_text(
            line,
            panel_left + 18,
            panel_top - 68,
            color=arcade.color.WHITE,
            font_size=13,
            width=panel_right - panel_left - 36,
            multiline=True,
        )

        if is_auto:
            footer = "They keep talking as you drive"
        elif self.dialogue_line_index < len(self.active_dialogue["lines"]) - 1:
            footer = "Press T to continue"
        else:
            footer = "Press T to let them speak again later"

        arcade.draw_text(
            footer,
            panel_left + 18,
            panel_bottom + 18,
            color=arcade.color.LIGHT_YELLOW,
            font_size=11,
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

        vanishing_x = WIDTH / 2
        for lane_idx in range(NUM_LANES + 1):
            bottom_x = lane_idx * LANE_WIDTH
            top_x = vanishing_x + (bottom_x - vanishing_x) * 0.16
            arcade.draw_line(
                start_x=bottom_x,
                start_y=0,
                end_x=top_x,
                end_y=HORIZON_Y,
                color=(180, 220, 255, int(20 * (1 - night) + 10 * night)),
                line_width=1,
            )

        road_left = (WIDTH * 0.5) - 260
        road_right = (WIDTH * 0.5) + 260
        arcade.draw_polygon_filled(
            [
                (road_left, 0),
                (road_right, 0),
                (WIDTH * 0.5 + 70, HORIZON_Y),
                (WIDTH * 0.5 - 70, HORIZON_Y),
            ],
            (14, 52, 92, 80),
        )

    def draw_boat(self):
        """Draw the player as a small boat."""
        x, y, scale = self.project_player(self.player_sprite.center_x, self.player_sprite.center_y)
        boat_width = 36 * scale
        boat_height = 24 * scale
        sail_height = 28 * scale

        arcade.draw_ellipse_filled(x + 2, y - 8 * scale, boat_width * 0.95, 10 * scale, (0, 0, 0, 70))
        arcade.draw_polygon_filled(
            [
                (x - boat_width * 0.5, y - boat_height * 0.35),
                (x + boat_width * 0.5, y - boat_height * 0.35),
                (x + boat_width * 0.33, y - boat_height * 1.05),
                (x - boat_width * 0.33, y - boat_height * 1.05),
            ],
            (108, 62, 30),
        )
        arcade.draw_polygon_filled(
            [
                (x - boat_width * 0.45, y - boat_height * 0.28),
                (x + boat_width * 0.45, y - boat_height * 0.28),
                (x + boat_width * 0.28, y - boat_height * 0.92),
                (x - boat_width * 0.28, y - boat_height * 0.92),
            ],
            (165, 96, 52),
        )
        arcade.draw_rect_filled(
            arcade.LRBT(left=x - 7 * scale, right=x + 7 * scale, bottom=y - 4 * scale, top=y + 7 * scale),
            color=(230, 235, 240),
        )
        arcade.draw_triangle_filled(
            x - 2 * scale,
            y + sail_height,
            x - 2 * scale,
            y - 2 * scale,
            x + 17 * scale,
            y + 6 * scale,
            (245, 248, 255),
        )
        arcade.draw_triangle_filled(
            x - 2 * scale,
            y + sail_height * 0.95,
            x - 2 * scale,
            y + 1 * scale,
            x - 18 * scale,
            y + 7 * scale,
            (210, 220, 230),
        )
        arcade.draw_line(x - 2 * scale, y + sail_height, x - 2 * scale, y - 14 * scale, (80, 50, 30), max(1, int(2 * scale)))
        arcade.draw_line(x - 16 * scale, y - 10 * scale, x + 16 * scale, y - 10 * scale, (255, 255, 255, 80), max(1, int(2 * scale)))
        arcade.draw_circle_filled(x, y - 2 * scale, max(1, int(3 * scale)), (255, 255, 255))

    def project_player(self, x, y):
        """Project the player into the forward-looking view."""
        return x, y, 1.0

    def draw_energy_drain_overlay(self):
        """Darken the scene as stamina gets low."""
        energy_ratio = max(0.0, min(1.0, self.energy / ENERGY_MAX))
        if energy_ratio >= LOW_ENERGY_THRESHOLD:
            return

        if energy_ratio <= LOW_ENERGY_FULL_DARK:
            alpha = 170
        else:
            t = (LOW_ENERGY_THRESHOLD - energy_ratio) / (LOW_ENERGY_THRESHOLD - LOW_ENERGY_FULL_DARK)
            alpha = int(70 + (120 * t))

        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=0, top=HEIGHT),
            color=(0, 0, 0, alpha),
        )

    def on_update(self, delta_time):
        """Update game logic."""
        if self.state == STATE_INTRO:
            self.intro_timer += delta_time
        elif self.state == STATE_AREA_TRANSITION:
            pass
        elif self.state == STATE_PLAYING:
            if self.dialogue_cooldown > 0:
                self.dialogue_cooldown = max(0.0, self.dialogue_cooldown - delta_time)
            if self.dialogue_mode == "manual":
                self.update_particles()
                return
            self.update_game(delta_time)
            self.update_auto_dialogue(delta_time)
        elif self.state == STATE_GAME_OVER:
            self.update_particles()

    def update_game(self, delta_time):
        """Update main game state."""
        self.game_time += delta_time
        self.distance += delta_time * 32
        self.area_timer += delta_time
        self.energy -= self.energy_drain_rate * delta_time

        if self.food_use_cooldown > 0:
            self.food_use_cooldown = max(0.0, self.food_use_cooldown - delta_time)

        if self.area < len(self.area_descriptions) and self.area_timer > 38:
            self.area += 1
            self.area_timer = 0
            self.energy = min(ENERGY_MAX, self.energy + AREA_ENERGY_BONUS)
            self.food += AREA_FOOD_BONUS
            self.refresh_control_mode()
            self.reset_dialogue_state()
            self.state = STATE_AREA_TRANSITION
            return

        if self.control_mode == "lane":
            self.player_sprite.center_x += (
                self.target_x - self.player_sprite.center_x
            ) * self.lane_lerp_speed
            self.player_sprite.center_y += (
                self.target_y - self.player_sprite.center_y
            ) * self.lane_lerp_speed
        else:
            self.update_free_movement(delta_time)

        self.obstacle_speed = BASE_OBSTACLE_SPEED + (self.game_time * OBSTACLE_SPEED_RAMP) + (self.area * 0.32)
        if self.area == 2:
            self.obstacle_speed += 0.2
        elif self.area >= 4:
            self.obstacle_speed += 0.65

        spawn_rate = max(MIN_SPAWN_INTERVAL, BASE_SPAWN_INTERVAL - (self.game_time * 0.008))
        self.spawn_timer += delta_time
        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0.0
            self.spawn_wave()

        pickup_speed = self.obstacle_speed * 0.92
        for pickup in self.food_pickups[:]:
            pickup.update(pickup_speed)
            if pickup.sprite.top < 0:
                self.food_pickups.remove(pickup)

        for obstacle in self.obstacle_list[:]:
            if isinstance(obstacle, CoastguardObstacle):
                obstacle.update(self.obstacle_speed, self.player_sprite.center_x)
                obstacle.check_spotted(self.player_sprite.center_x)
            else:
                obstacle.update(self.obstacle_speed)

            if obstacle.sprite.top < 0:
                self.recycle_obstacle(obstacle)

        for pickup in self.food_pickups[:]:
            if arcade.check_for_collision(self.player_sprite, pickup.sprite):
                self.food += 1
                self.create_food_burst(
                    self.player_sprite.center_x,
                    self.player_sprite.center_y,
                )
                self.food_pickups.remove(pickup)

        for obstacle in self.obstacle_list[:]:
            if arcade.check_for_collision(self.player_sprite, obstacle.sprite):
                if isinstance(obstacle, CoastguardObstacle) and obstacle.spotted:
                    self.game_over_event()
                else:
                    self.energy -= 46
                    self.create_explosion(
                        self.player_sprite.center_x,
                        self.player_sprite.center_y,
                    )
                    self.obstacle_list.remove(obstacle)

        self.update_particles()

        if self.energy <= 0:
            self.game_over_event()
            return

        self.update_dialogue_triggers()

    def current_dialogue_stage(self):
        """Return the dialogue set for the current area."""
        stage_index = min(self.area - 1, len(self.migrant_dialogues) - 1)
        return self.migrant_dialogues[stage_index]

    def stage_progress_distance(self):
        """Return how far the player is into the current area."""
        return self.area_timer * 32

    def reset_dialogue_state(self):
        """Clear all dialogue state when a stage changes."""
        self.dialogue_open = False
        self.dialogue_mode = None
        self.manual_dialogue_index = 0
        self.auto_dialogue_index = 0
        self.dialogue_line_index = 0
        self.dialogue_cooldown = 0.0
        self.dialogue_line_timer = 0.0
        self.active_dialogue = None

    def manual_dialogue_available(self):
        """Return True when a player-initiated talk point is ready."""
        if self.dialogue_open or self.dialogue_cooldown > 0:
            return False
        stage = self.current_dialogue_stage()
        manual_dialogues = stage["manual"]
        if self.manual_dialogue_index >= len(manual_dialogues):
            return False
        return self.stage_progress_distance() >= manual_dialogues[self.manual_dialogue_index]["trigger_distance"]

    def update_dialogue_triggers(self):
        """Start manual or auto conversations when their trigger points are reached."""
        if self.dialogue_open or self.dialogue_cooldown > 0:
            return

        stage = self.current_dialogue_stage()
        progress = self.stage_progress_distance()

        next_auto = self.next_auto_dialogue()
        if next_auto is not None and progress >= next_auto["trigger_distance"]:
            self.start_dialogue(next_auto, mode="auto")
            self.auto_dialogue_index += 1
            return

    def next_manual_dialogue(self):
        """Return the next manual dialogue beat for the current stage."""
        stage = self.current_dialogue_stage()
        manual_dialogues = stage["manual"]
        if self.manual_dialogue_index >= len(manual_dialogues):
            return None
        return manual_dialogues[self.manual_dialogue_index]

    def next_auto_dialogue(self):
        """Return the next automatic dialogue beat for the current stage."""
        stage = self.current_dialogue_stage()
        auto_dialogues = stage["auto"]
        if self.auto_dialogue_index >= len(auto_dialogues):
            return None
        return auto_dialogues[self.auto_dialogue_index]

    def start_dialogue(self, dialogue, mode):
        """Begin a dialogue in either manual or auto mode."""
        self.active_dialogue = dialogue
        self.dialogue_line_index = 0
        self.dialogue_open = True
        self.dialogue_mode = mode
        self.dialogue_line_timer = 0.0

    def advance_dialogue(self):
        """Advance or close the active passenger dialogue."""
        if self.active_dialogue is None:
            next_manual = self.next_manual_dialogue()
            if next_manual is None or self.stage_progress_distance() < next_manual["trigger_distance"]:
                return
            self.start_dialogue(next_manual, mode="manual")
            return

        if self.dialogue_mode == "auto":
            return

        if self.dialogue_line_index < len(self.active_dialogue["lines"]) - 1:
            self.dialogue_line_index += 1
            return

        self.dialogue_open = False
        self.dialogue_cooldown = 1.25
        self.manual_dialogue_index += 1
        self.active_dialogue = None
        self.dialogue_line_index = 0
        self.dialogue_mode = None
        self.dialogue_line_timer = 0.0

    def update_auto_dialogue(self, delta_time):
        """Advance auto dialogue lines while the boat is still moving."""
        if self.dialogue_mode != "auto" or self.active_dialogue is None:
            return

        self.dialogue_line_timer += delta_time
        if self.dialogue_line_timer < 2.4:
            return

        self.dialogue_line_timer = 0.0
        if self.dialogue_line_index < len(self.active_dialogue["lines"]) - 1:
            self.dialogue_line_index += 1
            return

        self.dialogue_open = False
        self.dialogue_cooldown = 1.0
        self.active_dialogue = None
        self.dialogue_line_index = 0
        self.dialogue_mode = None

    def update_free_movement(self, delta_time):
        """Move the boat freely in the later stages."""
        move_step = self.player_move_speed * delta_time

        if arcade.key.A in self.keys_down:
            self.player_sprite.center_x -= move_step
        if arcade.key.D in self.keys_down:
            self.player_sprite.center_x += move_step
        if arcade.key.W in self.keys_down:
            self.player_sprite.center_y += move_step * 0.9
        if arcade.key.S in self.keys_down:
            self.player_sprite.center_y -= move_step * 0.9

        self.player_sprite.center_x = max(
            PLAYER_SIZE / 2,
            min(WIDTH - PLAYER_SIZE / 2, self.player_sprite.center_x),
        )
        self.player_sprite.center_y = max(
            PLAYER_MIN_Y,
            min(PLAYER_MAX_Y, self.player_sprite.center_y),
        )

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
                self.manual_dialogue_index = 0
                self.auto_dialogue_index = 0
                self.dialogue_cooldown = 0.0
                self.active_dialogue = None

        elif self.state == STATE_PLAYING:
            if key == MIGRANT_DIALOGUE_KEY:
                self.advance_dialogue()
                return

            self.keys_down.add(key)

            if self.control_mode == "lane":
                if key in (arcade.key.LEFT, arcade.key.A) and self.player_lane > 0:
                    self.player_lane -= 1
                    self.target_x = LANES[self.player_lane]

                elif key in (arcade.key.RIGHT, arcade.key.D) and self.player_lane < NUM_LANES - 1:
                    self.player_lane += 1
                    self.target_x = LANES[self.player_lane]

            if key == arcade.key.SPACE and self.food > 0 and self.food_use_cooldown <= 0:
                self.energy = min(ENERGY_MAX, self.energy + ENERGY_PER_FOOD)
                self.food -= 1
                self.food_use_cooldown = 1.0

    def on_key_release(self, key, modifiers):
        """Track held keys for free movement."""
        if key in self.keys_down:
            self.keys_down.remove(key)

        elif self.state == STATE_GAME_OVER:
            if key == arcade.key.R:
                self.state = STATE_INTRO
                self.intro_index = 0


def main():
    RunnerGame()
    arcade.run()


if __name__ == "__main__":
    main()
