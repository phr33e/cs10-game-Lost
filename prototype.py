import arcade
import random

# --- Screen configuration ---
NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 600
TITLE = "20-Lane Runner – Neon Overdrive"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]
PLAYER_Y = 80
PLAYER_SIZE = LANE_WIDTH - 12
LERP_SPEED = 0.25  # How fast the player slides (0.0 to 1.0)

class RunnerGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        arcade.set_background_color((5, 5, 15)) # Deep space midnight

        self.player_sprite = None
        self.obstacle_list = None
        self.particles = None

        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]
        self.score = 0
        self.best_score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

        self.setup()

    def setup(self):
        self.obstacle_list = arcade.SpriteList()
        self.particles = arcade.SpriteList()

        # Player setup
        self.player_lane = NUM_LANES // 2
        self.target_x = LANES[self.player_lane]
        self.player_sprite = arcade.SpriteSolidColor(PLAYER_SIZE, PLAYER_SIZE, arcade.color.CYAN)
        self.player_sprite.center_x = self.target_x
        self.player_sprite.center_y = PLAYER_Y

        self.score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.game_time = 0.0
        self.obstacle_speed = 7.0

    def spawn_wave(self):
        # Increased difficulty: spawn more lanes as time goes on
        num_obstacles = random.randint(2, min(7, 2 + int(self.game_time // 10)))
        lanes_to_use = random.sample(LANES, k=num_obstacles)

        for x in lanes_to_use:
            # Variety in obstacle height
            h = random.choice([20, 40, 60])
            color = random.choice([arcade.color.ELECTRIC_CRIMSON, arcade.color.MAGENTA, arcade.color.HOT_PINK])

            obs = arcade.SpriteSolidColor(LANE_WIDTH - 4, h, color)
            obs.center_x = x
            obs.center_y = HEIGHT + 50
            self.obstacle_list.append(obs)

    def create_explosion(self, x, y):
        """Create a simple particle burst."""
        for _ in range(15):
            particle = arcade.SpriteSolidColor(6, 6, arcade.color.CYAN)
            particle.center_x = x
            particle.center_y = y
            particle.change_x = random.uniform(-5, 5)
            particle.change_y = random.uniform(-5, 5)
            self.particles.append(particle)

    def on_draw(self):
        self.clear()

        # Draw Lane Lines with a subtle glow
        for x in range(0, WIDTH + 1, LANE_WIDTH):
            arcade.draw_line(x, 0, x, HEIGHT, (40, 40, 80), 1)

        # Draw Obstacles with "Glow" (drawing twice)
        for obs in self.obstacle_list:
            # The glow
            arcade.draw_rectangle_filled(obs.center_x, obs.center_y, obs.width + 6, obs.height + 6, (*obs.color, 80))
            # The core
            obs.draw()

        # Draw Player with Glow
        if not self.game_over:
            arcade.draw_rectangle_filled(self.player_sprite.center_x, self.player_sprite.center_y,
                                         PLAYER_SIZE + 10, PLAYER_SIZE + 10, (0, 255, 255, 100))
            self.player_sprite.draw()

        self.particles.draw()

        # UI
        arcade.draw_text(f"SCORE: {int(self.score)}", 20, HEIGHT - 30, arcade.color.WHITE, 16, bold=True)
        arcade.draw_text(f"BEST: {int(self.best_score)}", WIDTH - 120, HEIGHT - 30, arcade.color.GRAY, 14)

        if self.game_over:
            arcade.draw_rectangle_filled(WIDTH/2, HEIGHT/2, 300, 100, (0, 0, 0, 200))
            arcade.draw_text("CRASHED", WIDTH/2, HEIGHT/2 + 10, arcade.color.RED, 24, align="center", anchor_x="center", bold=True)
            arcade.draw_text("Press R to Reboot", WIDTH/2, HEIGHT/2 - 20, arcade.color.WHITE, 14, align="center", anchor_x="center")

    def on_update(self, delta_time: float):
        if self.game_over:
            self.particles.update()
            return

        self.game_time += delta_time
        self.score += delta_time * 100

        # Smooth Player Movement (Lerp)
        self.player_sprite.center_x += (self.target_x - self.player_sprite.center_x) * LERP_SPEED

        # Difficulty & Spawning
        self.obstacle_speed = 7.0 + (self.game_time * 0.5)
        self.spawn_timer += delta_time
        if self.spawn_timer >= max(0.15, 0.7 - (self.game_time * 0.02)):
            self.spawn_timer = 0.0
            self.spawn_wave()

        # Move and Clean Obstacles
        for obs in self.obstacle_list:
            obs.center_y -= self.obstacle_speed
            if obs.top < 0:
                obs.remove_from_sprite_lists()

        # Collision
        if arcade.check_for_collision_with_list(self.player_sprite, self.obstacle_list):
            self.game_over = True
            self.best_score = max(self.best_score, self.score)
            self.create_explosion(self.player_sprite.center_x, self.player_sprite.center_y)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A) and self.player_lane > 0:
            self.player_lane -= 1
            self.target_x = LANES[self.player_lane]
        elif key in (arcade.key.RIGHT, arcade.key.D) and self.player_lane < NUM_LANES - 1:
            self.player_lane += 1
            self.target_x = LANES[self.player_lane]
        elif key == arcade.key.R and self.game_over:
            self.setup()

def main():
    game = RunnerGame()
    arcade.run()

if __name__ == "__main__":
    main()
