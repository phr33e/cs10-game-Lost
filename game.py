import arcade
import random

# Game Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Neon Lane Runner"

# Lane setup
LANE_WIDTH = SCREEN_WIDTH // 3
LANES = [
    LANE_WIDTH // 2,                  # Left lane center
    LANE_WIDTH + LANE_WIDTH // 2,     # Middle lane center
    LANE_WIDTH * 2 + LANE_WIDTH // 2  # Right lane center
]

class NeonRunner(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        # Game states: "START", "PLAYING", "GAME_OVER"
        self.state = "START"

        # Player attributes
        self.player_lane = 1
        self.player_x = LANES[self.player_lane]
        self.player_y = 100
        self.player_target_x = LANES[self.player_lane]

        # Obstacles and mechanics
        self.obstacles = []
        self.score = 0
        self.speed_multiplier = 1.0
        self.spawn_timer = 0
        self.spawn_rate = 70  # Frames between obstacle spawns

    def setup(self):
        """Reset the game state for a new run."""
        self.state = "PLAYING"
        self.player_lane = 1
        self.player_x = LANES[1]
        self.player_target_x = LANES[1]
        self.obstacles = []
        self.score = 0
        self.speed_multiplier = 1.0
        self.spawn_timer = 0

    def on_draw(self):
        """Render the screen."""
        self.clear()

        if self.state == "START":
            self.draw_start_screen()
        elif self.state == "PLAYING":
            self.draw_gameplay()
        elif self.state == "GAME_OVER":
            self.draw_game_over_screen()

    def draw_start_screen(self):
        arcade.draw_text("NEON RUNNER", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150,
                         arcade.color.NEON_CARROT, 28, anchor_x="center", font_name="Courier New", bold=True)

        arcade.draw_text("Avoid Obstacles.\nNo jumping. No sliding.\nPure reflexes.",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                         arcade.color.WHITE, 15, anchor_x="center", font_name="Courier New", align="center")

        arcade.draw_text("Controls: A/D or Left/Right Arrow Keys", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
                         arcade.color.YELLOW, 12, anchor_x="center", font_name="Courier New")

        arcade.draw_text("Press ENTER to Start", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 160,
                         arcade.color.GREEN, 18, anchor_x="center", font_name="Courier New", bold=True)

    def draw_gameplay(self):
        # Draw Lane Dividers (dotted lines)
        for x_pos in [LANE_WIDTH, LANE_WIDTH * 2]:
            arcade.draw_line(x_pos, 0, x_pos, SCREEN_HEIGHT, arcade.color.DARK_GRAY, 3)

        # Draw Obstacles (Pink neon blocks)
        for obs in self.obstacles:
            arcade.draw_rectangle_filled(
                obs['x'], obs['y'],
                LANE_WIDTH - 40, 40,
                arcade.color.FLUORESCENT_PINK
            )

        # Draw Player (Cyan triangle pointing upward)
        arcade.draw_triangle_filled(
            self.player_x, self.player_y + 20,
            self.player_x - 18, self.player_y - 18,
            self.player_x + 18, self.player_y - 18,
            arcade.color.NEON_BLUE
        )

        # Draw HUD (Score and Speed)
        arcade.draw_text(f"SCORE: {int(self.score)}", 20, SCREEN_HEIGHT - 40,
                         arcade.color.YELLOW, 16, font_name="Courier New", bold=True)
        arcade.draw_text(f"x{self.speed_multiplier:.1f} SPD", SCREEN_WIDTH - 20, SCREEN_HEIGHT - 40,
                         arcade.color.GREEN, 16, anchor_x="right", font_name="Courier New", bold=True)

    def draw_game_over_screen(self):
        arcade.draw_text("GAME OVER", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200,
                         arcade.color.RED, 32, anchor_x="center", font_name="Courier New", bold=True)

        arcade.draw_text(f"FINAL SCORE: {int(self.score)}", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                         arcade.color.WHITE, 20, anchor_x="center", font_name="Courier New")

        arcade.draw_text("Press ENTER to Play Again", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                         arcade.color.GREEN, 16, anchor_x="center", font_name="Courier New", bold=True)

    def on_update(self, delta_time):
        """All movement and game logic happens here."""
        if self.state != "PLAYING":
            return

        # 1. Score tracking & Speed progression
        self.score += 0.15
        self.speed_multiplier = 1.0 + (self.score / 250.0)

        # 2. Smooth player movement transition
        dx = self.player_target_x - self.player_x
        self.player_x += dx * 0.3  # Linear interpolation for sliding feel

        # 3. Handle obstacle spawning
        self.spawn_timer += 1
        current_spawn_rate = max(25, self.spawn_rate - int(self.score / 15))
        if self.spawn_timer >= current_spawn_rate:
            lane = random.randint(0, 2)
            self.obstacles.append({
                'x': LANES[lane],
                'y': SCREEN_HEIGHT + 30,
                'lane': lane
            })
            self.spawn_timer = 0

        # 4. Move obstacles & Check Collisions
        for obs in self.obstacles[:]:
            obs['y'] -= 6 * self.speed_multiplier

            # Clean up out-of-bounds obstacles
            if obs['y'] < -50:
                self.obstacles.remove(obs)
                continue

            # Collision Math: Box check (Obstacle width/height + player tolerance margin)
            obs_half_width = (LANE_WIDTH - 40) / 2
            obs_half_height = 20

            if (abs(self.player_x - obs['x']) < (obs_half_width + 12) and
                abs(self.player_y - obs['y']) < (obs_half_height + 15)):
                self.state = "GAME_OVER"

    def on_key_press(self, key, modifiers):
        """Handle keyboard inputs."""
        if self.state in ["START", "GAME_OVER"]:
            if key == arcade.key.ENTER:
                self.setup()
            return

        if self.state == "PLAYING":
            if key in [arcade.key.LEFT, arcade.key.A]:
                if self.player_lane > 0:
                    self.player_lane -= 1
                    self.player_target_x = LANES[self.player_lane]
            elif key in [arcade.key.RIGHT, arcade.key.D]:
                if self.player_lane < 2:
                    self.player_lane += 1
                    self.player_target_x = LANES[self.player_lane]

def main():
    game = NeonRunner()
    arcade.run()

if __name__ == "__main__":
    main()
