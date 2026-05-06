import arcade
import random

# --- Screen configuration ---
NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 600
TITLE = "20-Lane Runner – Neon Lanes"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

PLAYER_Y = 80
PLAYER_SIZE = LANE_WIDTH - 10


class RunnerGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        # Sprite lists
        self.bg_list = arcade.SpriteList()
        self.lane_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.obstacle_list = arcade.SpriteList()
        self.hud_list = arcade.SpriteList()

        # Game state
        self.player_lane = NUM_LANES // 2
        self.player_sprite = None

        self.score = 0
        self.best_score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

        self.setup()

    def setup(self):
        # Clear sprites
        self.bg_list = arcade.SpriteList()
        self.lane_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.obstacle_list = arcade.SpriteList()
        self.hud_list = arcade.SpriteList()

        # Background gradient effect: 3 tall bands
        band_height = HEIGHT // 3
        band_colors = [
            (10, 10, 40),   # dark blueish
            (15, 5, 50),    # purple
            (5, 10, 35),    # teal
        ]
        for i, color in enumerate(band_colors):
            band = arcade.SpriteSolidColor(WIDTH, band_height, color)
            band.center_x = WIDTH // 2
            band.center_y = band_height * i + band_height // 2
            self.bg_list.append(band)

        # Lane markers: alternating neon colors
        lane_colors = [arcade.color.DARK_GRAY, (60, 60, 120)]
        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            color = lane_colors[i % 2]
            lane = arcade.SpriteSolidColor(2, HEIGHT, color)
            lane.center_x = x
            lane.center_y = HEIGHT // 2
            self.lane_list.append(lane)

        # Player
        self.player_lane = NUM_LANES // 2
        self.player_sprite = arcade.SpriteSolidColor(
            PLAYER_SIZE, PLAYER_SIZE, arcade.color.CYAN
        )
        self.player_sprite.center_x = LANES[self.player_lane]
        self.player_sprite.center_y = PLAYER_Y
        self.player_list.append(self.player_sprite)

        # HUD bar
        hud_bg = arcade.SpriteSolidColor(WIDTH, 40, (0, 0, 0, 220))
        hud_bg.center_x = WIDTH // 2
        hud_bg.center_y = HEIGHT - 20
        self.hud_list.append(hud_bg)

        # Reset game state
        self.score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

    def spawn_wave(self):
        """Spawn a wave of mixed obstacle types."""
        lanes_to_use = random.sample(LANES, k=random.randint(2, 5))

        for x in lanes_to_use:
            shape_type = random.choice(["block", "tall", "wide"])

            if shape_type == "block":
                w, h = LANE_WIDTH - 6, 26
                color = arcade.color.RED_ORANGE
            elif shape_type == "tall":
                w, h = LANE_WIDTH - 14, 44
                color = arcade.color.ORANGE_PEEL
            else:  # wide
                w, h = LANE_WIDTH - 2, 18
                color = arcade.color.MAGENTA

            obs = arcade.SpriteSolidColor(w, h, color)
            obs.center_x = x
            obs.center_y = HEIGHT + 40
            self.obstacle_list.append(obs)

    # --- Drawing ---

    def on_draw(self):
        self.clear()

        # Background & lanes
        self.bg_list.draw()
        self.lane_list.draw()

        # Obstacles and player
        self.obstacle_list.draw()
        self.player_list.draw()

        # HUD bar
        self.hud_list.draw()

        # HUD text
        arcade.draw_text(
            f"SCORE: {self.score}",
            10,
            HEIGHT - 32,
            arcade.color.WHITE,
            16,
        )
        arcade.draw_text(
            f"BEST: {self.best_score}",
            200,
            HEIGHT - 32,
            arcade.color.LIGHT_GRAY,
            14,
        )

        if self.game_over:
            arcade.draw_text(
                "GAME OVER",
                WIDTH / 2,
                HEIGHT / 2 + 20,
                arcade.color.YELLOW,
                24,
                anchor_x="center",
            )
            arcade.draw_text(
                "Press R to restart",
                WIDTH / 2,
                HEIGHT / 2 - 10,
                arcade.color.WHITE,
                16,
                anchor_x="center",
            )

    # --- Game logic ---

    def on_update(self, delta_time: float):
        if self.game_over:
            return

        self.game_time += delta_time
        self.score += 1

        # Difficulty scaling
        self.obstacle_speed = 7.0 + self.game_time * 0.4

        # Spawn faster as you survive longer
        self.spawn_timer += delta_time
        spawn_interval = max(0.2, 0.85 - self.game_time * 0.03)

        if self.spawn_timer >= spawn_interval:
            self.spawn_timer = 0.0
            self.spawn_wave()

        # Move obstacles down
        for obs in self.obstacle_list:
            obs.center_y -= self.obstacle_speed

        # Collision detection
        hits = arcade.check_for_collision_with_list(
            self.player_sprite, self.obstacle_list
        )
        if hits:
            self.game_over = True
            self.best_score = max(self.best_score, self.score)

        # Remove off-screen obstacles
        for obs in self.obstacle_list[:]:
            if obs.top < -40:
                obs.remove_from_sprite_lists()

    # --- Input ---

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            if self.player_lane > 0:
                self.player_lane -= 1
                self.player_sprite.center_x = LANES[self.player_lane]

        elif key in (arcade.key.RIGHT, arcade.key.D):
            if self.player_lane < NUM_LANES - 1:
                self.player_lane += 1
                self.player_sprite.center_x = LANES[self.player_lane]

        elif key == arcade.key.R and self.game_over:
            self.setup()


def main():
    RunnerGame()
    arcade.run()


if __name__ == "__main__":
    main()
