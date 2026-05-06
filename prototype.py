import arcade
import random

# --- Screen configuration ---
NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 600
TITLE = "20-Lane Runner – Sprite-Only"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

PLAYER_Y = 80
PLAYER_SIZE = LANE_WIDTH - 10

OBSTACLE_WIDTH = LANE_WIDTH - 6
OBSTACLE_HEIGHT = 30


class RunnerGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)

        # Background color is just the clear color; no draw_rectangle
        arcade.set_background_color(arcade.color.BLACK)

        # SpriteLists
        self.lane_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.obstacle_list = arcade.SpriteList()
        self.hud_list = arcade.SpriteList()

        # Game state
        self.player_lane = NUM_LANES // 2
        self.player_sprite = None

        self.score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

        self.setup()

    def setup(self):
        # Clear any existing sprites
        self.lane_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.obstacle_list = arcade.SpriteList()
        self.hud_list = arcade.SpriteList()

        # Lanes: thin vertical sprites
        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            lane = arcade.SpriteSolidColor(2, HEIGHT, arcade.color.DARK_GRAY)
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
        hud_bg = arcade.SpriteSolidColor(WIDTH, 40, (0, 0, 0, 180))
        hud_bg.center_x = WIDTH // 2
        hud_bg.center_y = HEIGHT - 20
        self.hud_list.append(hud_bg)

        # Game state
        self.score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

    # --- Drawing ---

    def on_draw(self):
        self.clear()

        # Draw lanes, player, obstacles, HUD background
        self.lane_list.draw()
        self.obstacle_list.draw()
        self.player_list.draw()
        self.hud_list.draw()

        # Text is still drawn with draw_text
        arcade.draw_text(
            f"SCORE: {self.score}",
            10,
            HEIGHT - 32,
            arcade.color.WHITE,
            16,
        )

        if self.game_over:
            arcade.draw_text(
                "GAME OVER - Press R to restart",
                WIDTH / 2,
                HEIGHT / 2,
                arcade.color.YELLOW,
                18,
                anchor_x="center",
            )

    # --- Game logic ---

    def on_update(self, delta_time: float):
        if self.game_over:
            return

        self.game_time += delta_time
        self.score += 1

        # Scale difficulty
        self.obstacle_speed = 7.0 + self.game_time * 0.4

        # Spawn obstacles
        self.spawn_timer += delta_time
        spawn_interval = max(0.25, 0.9 - self.game_time * 0.04)

        if self.spawn_timer >= spawn_interval:
            self.spawn_timer = 0.0
            lane_xs = random.sample(LANES, k=random.randint(1, 3))
            for x in lane_xs:
                obs = arcade.SpriteSolidColor(
                    OBSTACLE_WIDTH, OBSTACLE_HEIGHT, arcade.color.RED
                )
                obs.center_x = x
                obs.center_y = HEIGHT + 40
                self.obstacle_list.append(obs)

        # Move obstacles
        for obs in self.obstacle_list:
            obs.center_y -= self.obstacle_speed

        # Collision detection: use Arcade helper
        hits = arcade.check_for_collision_with_list(
            self.player_sprite, self.obstacle_list
        )
        if hits:
            self.game_over = True

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
