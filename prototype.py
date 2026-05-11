import arcade
import random
import math

# --- Screen configuration ---
NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 600
TITLE = "The Journey – Lampedusa"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]
PLAYER_Y = 80
PLAYER_SIZE = LANE_WIDTH - 12
LERP_SPEED = 0.2
ENERGY_DRAIN_RATE = 8.0
ENERGY_MAX = 100
ENERGY_PER_FOOD = 40

# Game States
STATE_INTRO = "intro"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_AREA_TRANSITION = "area_transition"

class Obstacle:
    """Base obstacle class"""
    def __init__(self, x, y, width, height, color, speed=None):
        self.sprite = arcade.SpriteSolidColor(width=width, height=height, color=color)
        self.sprite.center_x = x
        self.sprite.center_y = y
        self.speed = speed
        self.color = color
        self.width = width
        self.height = height

    def update(self, obstacle_speed):
        self.sprite.center_y -= obstacle_speed

    def draw_with_glow(self):
        arcade.draw_rect_filled(
            arcade.LRBT(
                left=self.sprite.left - 4,
                right=self.sprite.right + 4,
                bottom=self.sprite.bottom - 4,
                top=self.sprite.top + 4
            ),
            color=(*self.color, 80)
        )
        self.sprite.draw()

class TideObstacle(Obstacle):
    """Faster moving obstacle"""
    pass

class CurrentObstacle(Obstacle):
    """Traps player in specific lanes"""
    def __init__(self, x, y, width, height, color, trapped_lanes):
        super().__init__(x, y, width, height, color)
        self.trapped_lanes = trapped_lanes

class CoastguardObstacle(Obstacle):
    """Chases player if spotted"""
    def __init__(self, x, y):
        super().__init__(x, y, LANE_WIDTH - 8, 30, arcade.color.WHITE)
        self.spotted = False
        self.chase_timer = 0
        self.visibility_range = 150

    def check_spotted(self, player_x):
        distance = abs(player_x - self.sprite.center_x)
        if distance < self.visibility_range:
            self.spotted = True
            self.chase_timer = 300  # 5 seconds at 60 FPS

    def update(self, obstacle_speed, player_x=None):
        if self.spotted and player_x:
            direction = 1 if player_x > self.sprite.center_x else -1
            self.sprite.center_x += direction * 3
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

        # Core game objects
        self.player_sprite = None
        self.obstacle_list = []
        self.particles = arcade.SpriteList()

        # Player state
        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]
        self.energy = ENERGY_MAX
        self.food = 15
        self.score = 0
        self.best_score = 0
        self.distance = 0

        # Game progression
        self.game_time = 0.0
        self.spawn_timer = 0.0
        self.obstacle_speed = 7.0
        self.area = 1
        self.area_timer = 0
        self.area_lengths = [1500, 1800, 2000, 2200]  # Distance per area

        # Difficulty
        self.difficulty_multiplier = 1.0

        # Intro state
        self.intro_text = [
            "You are a sailor.",
            "Your family is waiting for you in Italy.",
            "You've been hired to guide a boat across the Mediterranean.",
            "Food and Energy are your only resources.",
            "Energy drains constantly. Food restores it.",
            "Hit obstacles to lose Energy. Lose all Energy, and the journey ends.",
            "Press SPACE to continue..."
        ]
        self.intro_index = 0
        self.intro_timer = 0

        # Area descriptions
        self.area_descriptions = [
            ("THE DEPARTURE", "Africa's coast fades behind. The sea is calm.\nWatch your Energy and ration your Food carefully."),
            ("OPEN WATERS", "Far from shore now. The currents are unpredictable.\nStay alert for unexpected obstacles."),
            ("THE NARROWS", "Cliffs close in from both sides. The channel narrows.\nOne wrong move and it's over."),
            ("FINAL STRETCH", "You can almost see the Lampedusa coast.\nThe Coastguard is active. Stay hidden. Don't get spotted.")
        ]

        self.setup()

    def setup(self):
        """Initialize game state"""
        self.state = STATE_PLAYING
        self.obstacle_list = []
        self.particles = arcade.SpriteList()

        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]

        self.player_sprite = arcade.SpriteSolidColor(
            width=PLAYER_SIZE,
            height=PLAYER_SIZE,
            color=arcade.color.CYAN
        )
        self.player_sprite.center_x = self.target_x
        self.player_sprite.center_y = PLAYER_Y

        self.energy = ENERGY_MAX
        self.food = 15
        self.score = 0
        self.distance = 0
        self.game_time = 0.0
        self.spawn_timer = 0.0
        self.obstacle_speed = 7.0
        self.area = 1
        self.area_timer = 0
        self.difficulty_multiplier = 1.0

    def spawn_wave(self):
        """Spawn obstacles based on current area"""
        if self.area == 1:
            self.spawn_basic_wave()
        elif self.area == 2:
            self.spawn_tidal_wave()
        elif self.area == 3:
            self.spawn_narrows_wave()
        else:
            self.spawn_coastguard_wave()

    def spawn_basic_wave(self):
        """Basic rocks"""
        num_obstacles = random.randint(1, min(4, 1 + int(self.game_time // 15)))
        lanes_to_use = random.sample(range(NUM_LANES), k=num_obstacles)

        for lane_idx in lanes_to_use:
            x = LANES[lane_idx]
            h = random.choice([20, 30, 40])
            col = random.choice([arcade.color.ELECTRIC_CRIMSON, arcade.color.MAGENTA, arcade.color.HOT_PINK])

            obs = Obstacle(x, HEIGHT + 50, LANE_WIDTH - 4, h, col)
            self.obstacle_list.append(obs)

    def spawn_tidal_wave(self):
        """Faster obstacles (tides)"""
        num_obstacles = random.randint(2, 5)
        lanes_to_use = random.sample(range(NUM_LANES), k=num_obstacles)

        for lane_idx in lanes_to_use:
            x = LANES[lane_idx]
            h = random.choice([25, 35, 45])
            col = arcade.color.LIGHT_BLUE_1

            obs = TideObstacle(x, HEIGHT + 50, LANE_WIDTH - 4, h, col, speed=self.obstacle_speed * 1.5)
            self.obstacle_list.append(obs)

    def spawn_narrows_wave(self):
        """Narrowing lanes - reduce available lanes over time"""
        available_lanes = max(8, NUM_LANES - int(self.area_timer // 2))
        lane_offset = (NUM_LANES - available_lanes) // 2

        num_obstacles = random.randint(3, 6)
        valid_lanes = list(range(lane_offset)) + list(range(NUM_LANES - lane_offset, NUM_LANES))

        if valid_lanes:
            lanes_to_use = random.sample(valid_lanes, k=min(num_obstacles, len(valid_lanes)))
            for lane_idx in lanes_to_use:
                x = LANES[lane_idx]
                obs = Obstacle(x, HEIGHT + 50, LANE_WIDTH - 4, random.choice([30, 40, 50]),
                             arcade.color.DARK_SLATE_GRAY)
                self.obstacle_list.append(obs)

    def spawn_coastguard_wave(self):
        """Coastguard boats that chase if spotted"""
        if random.random() < 0.3:
            x = random.choice(LANES)
            obs = CoastguardObstacle(x, HEIGHT + 50)
            self.obstacle_list.append(obs)
        else:
            self.spawn_basic_wave()

    def create_explosion(self, x, y):
        """Create particle explosion effect"""
        for _ in range(20):
            particle = arcade.SpriteSolidColor(width=6, height=6, color=arcade.color.ORANGE)
            particle.center_x = x + random.uniform(-10, 10)
            particle.center_y = y + random.uniform(-10, 10)
            particle.change_x = random.uniform(-6, 6)
            particle.change_y = random.uniform(-6, 6)
            particle.lifetime = 60
            self.particles.append(particle)

    def on_draw(self):
        """Render the game"""
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
        """Draw main game screen"""
        # 1. Lane dividers
        for x in range(0, WIDTH + 1, LANE_WIDTH):
            arcade.draw_line(start_x=x, start_y=0, end_x=x, end_y=HEIGHT,
                           color=(40, 40, 80), line_width=1)

        # 2. Draw obstacles with glow
        for obs in self.obstacle_list:
            obs.draw_with_glow()

        # 3. Draw player with glow
        arcade.draw_rect_filled(
            arcade.LRBT(
                left=self.player_sprite.left - 6,
                right=self.player_sprite.right + 6,
                bottom=self.player_sprite.bottom - 6,
                top=self.player_sprite.top + 6
            ),
            color=(0, 255, 255, 100)
        )
        self.player_sprite.draw()

        # 4. Draw particles
        for particle in self.particles:
            particle.draw()

        # 5. HUD - Food bar
        bar_width = 200
        bar_height = 20
        bar_x = 20
        bar_y = HEIGHT - 35

        # Food bar background
        arcade.draw_rect_outline(
            arcade.LRBT(left=bar_x, right=bar_x + bar_width, bottom=bar_y, top=bar_y + bar_height),
            color=arcade.color.WHITE, border_width=2
        )

        # Food bar fill
        food_ratio = max(0, self.food / 15.0)
        food_color = arcade.color.GREEN if food_ratio > 0.3 else arcade.color.ORANGE if food_ratio > 0.1 else arcade.color.RED
        arcade.draw_rect_filled(
            arcade.LRBT(
                left=bar_x,
                right=bar_x + (bar_width * food_ratio),
                bottom=bar_y,
                top=bar_y + bar_height
            ),
            color=food_color
        )

        arcade.draw_text(f"FOOD: {int(self.food)}", bar_x + 210, bar_y + 2,
                        color=arcade.color.WHITE, font_size=14, bold=True)

        # 6. Score and distance
        arcade.draw_text(f"DISTANCE: {int(self.distance)}m", WIDTH - 180, HEIGHT - 35,
                        color=arcade.color.CYAN, font_size=14, bold=True)
        arcade.draw_text(f"AREA: {self.area}/4", WIDTH - 180, HEIGHT - 55,
                        color=arcade.color.LIGHT_CYAN, font_size=12)

    def draw_intro(self):
        """Draw introduction screen"""
        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=0, top=HEIGHT),
            color=(5, 5, 15)
        )

        arcade.draw_text("THE JOURNEY", WIDTH // 2, HEIGHT - 80,
                        color=arcade.color.CYAN, font_size=36, anchor_x="center", bold=True)
        arcade.draw_text("A Crossing to Lampedusa", WIDTH // 2, HEIGHT - 130,
                        color=arcade.color.LIGHT_CYAN, font_size=16, anchor_x="center")

        # Draw current intro text
        if self.intro_index < len(self.intro_text):
            text = self.intro_text[self.intro_index]
            arcade.draw_text(text, WIDTH // 2, HEIGHT // 2,
                            color=arcade.color.WHITE, font_size=14,
                            anchor_x="center", width=WIDTH - 100)

        arcade.draw_text("Press SPACE to continue", WIDTH // 2, 50,
                        color=arcade.color.GRAY, font_size=12, anchor_x="center")

    def draw_area_transition(self):
        """Draw area transition screen"""
        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=0, top=HEIGHT),
            color=(0, 0, 0)
        )

        if self.area <= len(self.area_descriptions):
            title, desc = self.area_descriptions[self.area - 1]
            arcade.draw_text(title, WIDTH // 2, HEIGHT // 2 + 50,
                            color=arcade.color.CYAN, font_size=28, anchor_x="center", bold=True)
            arcade.draw_text(desc, WIDTH // 2, HEIGHT // 2 - 20,
                            color=arcade.color.WHITE, font_size=14, anchor_x="center", width=WIDTH - 100)

        arcade.draw_text("Press SPACE to continue", WIDTH // 2, 50,
                        color=arcade.color.GRAY, font_size=12, anchor_x="center")

    def draw_game_over(self):
        """Draw game over screen"""
        # Semi-transparent overlay
        arcade.draw_rect_filled(
            arcade.LRBT(left=0, right=WIDTH, bottom=0, top=HEIGHT),
            color=(0, 0, 0, 180)
        )

        # Game Over box
        arcade.draw_rect_filled(
            arcade.LRBT(
                left=WIDTH // 2 - 180,
                right=WIDTH // 2 + 180,
                bottom=HEIGHT // 2 - 100,
                top=HEIGHT // 2 + 100
            ),
            color=(20, 20, 40)
        )

        arcade.draw_rect_outline(
            arcade.LRBT(
                left=WIDTH // 2 - 180,
                right=WIDTH // 2 + 180,
                bottom=HEIGHT // 2 - 100,
                top=HEIGHT // 2 + 100
            ),
            color=arcade.color.RED, border_width=3
        )

        arcade.draw_text("JOURNEY ENDED", WIDTH // 2, HEIGHT // 2 + 60,
                        color=arcade.color.RED, font_size=24, anchor_x="center", bold=True)
        arcade.draw_text(f"Distance Traveled: {int(self.distance)}m", WIDTH // 2, HEIGHT // 2 + 20,
                        color=arcade.color.WHITE, font_size=14, anchor_x="center")
        arcade.draw_text(f"Best Distance: {int(self.best_score)}m", WIDTH // 2, HEIGHT // 2 - 10,
                        color=arcade.color.LIGHT_CYAN, font_size=12, anchor_x="center")
        arcade.draw_text("Press R to Try Again", WIDTH // 2, HEIGHT // 2 - 60,
                        color=arcade.color.CYAN, font_size=14, anchor_x="center")

    def on_update(self, delta_time: float):
        """Update game logic"""
        if self.state == STATE_INTRO:
            self.intro_timer += delta_time
        elif self.state == STATE_AREA_TRANSITION:
            # Just wait for space press
            pass
        elif self.state == STATE_PLAYING:
            self.update_game(delta_time)
        elif self.state == STATE_GAME_OVER:
            # Update particles only
            self.update_particles(delta_time)

    def update_game(self, delta_time: float):
        """Update main game state"""
        self.game_time += delta_time
        self.distance += delta_time * 50  # Constant forward movement
        self.area_timer += delta_time

        # Energy drain
        self.energy -= ENERGY_DRAIN_RATE * delta_time

        # Check if reached next area
        if self.area < 4 and self.area_timer > 30:  # 30 seconds per area for demo
            self.area += 1
            self.area_timer = 0
            self.state = STATE_AREA_TRANSITION
            return

        # Smooth player movement
        self.player_sprite.center_x += (self.target_x - self.player_sprite.center_x) * LERP_SPEED

        # Update obstacle speed based on time/area
        self.obstacle_speed = 7.0 + (self.game_time * 0.3) + (self.area * 0.5)

        # Spawn obstacles
        spawn_rate = max(0.1, 0.6 - (self.game_time * 0.015))
        self.spawn_timer += delta_time
        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0.0
            self.spawn_wave()

        # Update obstacles
        for obs in self.obstacle_list[:]:
            if isinstance(obs, CoastguardObstacle):
                obs.update(self.obstacle_speed, self.player_sprite.center_x)
                obs.check_spotted(self.player_sprite.center_x)
            else:
                obs.update(self.obstacle_speed)

            if obs.sprite.top < 0:
                self.obstacle_list.remove(obs)

        # Collision detection
        for obs in self.obstacle_list:
            if arcade.has_line_of_sight(
                self.player_sprite.center_x,
                self.player_sprite.center_y,
                obs.sprite.center_x,
                obs.sprite.center_y,
                obstacles=None
            ):
                if arcade.check_for_collision(self.player_sprite, obs.sprite):
                    if isinstance(obs, CoastguardObstacle) and obs.spotted:
                        # Caught by coastguard
                        self.game_over_event()
                    else:
                        # Hit obstacle
                        self.energy -= 20
                        self.create_explosion(self.player_sprite.center_x, self.player_sprite.center_y)
                        self.obstacle_list.remove(obs)

        # Update particles
        self.update_particles(delta_time)

        # Check game over conditions
        if self.energy <= 0:
            self.game_over_event()

    def update_particles(self, delta_time: float):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle.center_x += particle.change_x
            particle.center_y += particle.change_y
            particle.change_y -= 0.2  # Gravity
            particle.lifetime -= 1
            particle.color = (255, int(255 * (particle.lifetime / 60)), 0)

            if particle.lifetime <= 0:
                self.particles.remove(particle)

    def game_over_event(self):
        """Handle game over"""
        self.state = STATE_GAME_OVER
        self.best_score = max(self.best_score, self.distance)
        if self.energy > 0:
            self.create_explosion(self.player_sprite.center_x, self.player_sprite.center_y)

    def on_key_press(self, key, modifiers):
        """Handle key presses"""
        if self.state == STATE_INTRO:
            if key == arcade.key.SPACE:
                self.intro_index += 1
                if self.intro_index >= len(self.intro_text):
                    self.setup()

        elif self.state == STATE_AREA_TRANSITION:
            if key == arcade.key.SPACE:
                self.state = STATE_PLAYING

        elif self.state == STATE_PLAYING:
            # Movement
            if key in (arcade.key.LEFT, arcade.key.A) and self.player_lane > 0:
                self.player_lane -= 1
                self.target_x = LANES[self.player_lane]
            elif key in (arcade.key.RIGHT, arcade.key.D) and self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.target_x = LANES[self.player_lane]

            # Use food
            if key == arcade.key.SPACE and self.food > 0:
                self.energy = min(ENERGY_MAX, self.energy + ENERGY_PER_FOOD)
                self.food -= 1

        elif self.state == STATE_GAME_OVER:
            if key == arcade.key.R:
                self.state = STATE_INTRO
                self.intro_index = 0

def main():
    window = RunnerGame()
    arcade.run()

if __name__ == "__main__":
    main()
