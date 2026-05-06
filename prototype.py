import arcade
import random
import math

NUM_LANES = 20
LANE_WIDTH = 40
WIDTH = NUM_LANES * LANE_WIDTH
HEIGHT = 720
TITLE = "20-Lane Runner (SpriteList-Only)"

LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(NUM_LANES)]

PLAYER_Y = 90
PLAYER_SIZE = LANE_WIDTH - 10

OBSTACLE_TYPES = [
    {"color": arcade.color.RED_ORANGE, "w": 34, "h": 28, "speed_mult": 1.0},
    {"color": arcade.color.MAGENTA, "w": 28, "h": 44, "speed_mult": 1.15},
    {"color": arcade.color.ORANGE, "w": 36, "h": 20, "speed_mult": 1.3},
]


class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.camera = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()

        self.time = 0.0

        # Sprite lists
        self.background_sprites = arcade.SpriteList()
        self.lane_sprites = arcade.SpriteList()
        self.road_stripes = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.obstacles = arcade.SpriteList()
        self.hud_sprites = arcade.SpriteList()
        self.overlay_sprites = arcade.SpriteList()

        self.player = None
        self.player_lane = 0
        self.target_lane = 0

        self.score = 0
        self.best_score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.scroll = 0.0
        self.speed = 360.0
        self.shake_time = 0.0
        self.shake_power = 0.0

        self.star_field = []

    def setup(self):
        self.time = 0.0

        self.background_sprites = arcade.SpriteList()
        self.lane_sprites = arcade.SpriteList()
        self.road_stripes = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.obstacles = arcade.SpriteList()
        self.hud_sprites = arcade.SpriteList()
        self.overlay_sprites = arcade.SpriteList()

        # Background
        bg = arcade.SpriteSolidColor(WIDTH, HEIGHT, (8, 8, 18))
        bg.center_x = WIDTH // 2
        bg.center_y = HEIGHT // 2
        self.background_sprites.append(bg)

        # Lanes
        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            lane_line = arcade.SpriteSolidColor(2, HEIGHT, (80, 80, 80))
            lane_line.center_x = x
            lane_line.center_y = HEIGHT // 2
            self.lane_sprites.append(lane_line)

        # Road stripes
        for y in range(-120, HEIGHT + 120, 120):
            stripe = arcade.SpriteSolidColor(WIDTH, 8, (20, 20, 26))
            stripe.center_x = WIDTH // 2
            stripe.center_y = y
            stripe.tag = "stripe"
            self.road_stripes.append(stripe)

        # Stars (drawn with primitive; if THAT also errors for you, we can remove them)
        self.star_field = []
        for _ in range(80):
            self.star_field.append(
                [random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)]
            )

        # Player
        self.player_lane = NUM_LANES // 2
        self.target_lane = self.player_lane

        self.player = arcade.SpriteSolidColor(PLAYER_SIZE, PLAYER_SIZE, arcade.color.CYAN)
        self.player.center_x = LANES[self.player_lane]
        self.player.center_y = PLAYER_Y
        self.player_list.append(self.player)

        # HUD bar as sprite
        hud_bg = arcade.SpriteSolidColor(WIDTH, 72, (0, 0, 0, 180))
        hud_bg.center_x = WIDTH // 2
        hud_bg.center_y = HEIGHT - 36
        self.hud_sprites.append(hud_bg)

        # Game state
        self.score = 0
        self.game_over = False
        self.spawn_timer = 0.0
        self.scroll = 0.0
        self.speed = 360.0
        self.shake_time = 0.0
        self.shake_power = 0.0

        # Clear overlays
        self.overlay_sprites = arcade.SpriteList()

    def spawn_obstacle(self):
        t = random.choice(OBSTACLE_TYPES)
        obstacle = arcade.SpriteSolidColor(t["w"], t["h"], t["color"])
        obstacle.center_x = random.choice(LANES)
        obstacle.center_y = HEIGHT + 60
        obstacle.change_y = -self.speed * t["speed_mult"]
        self.obstacles.append(obstacle)

    def on_draw(self):
        self.clear()

        # WORLD CAMERA
        self.camera.use()

        self.background_sprites.draw()
        self.lane_sprites.draw()
        self.road_stripes.draw()
        self.obstacles.draw()
        self.player_list.draw()

        # Stars (optional: comment this out if primitives cause issues)
        for x, y, s in self.star_field:
            arcade.draw_circle_filled(x, y, s, arcade.color.WHITE)

        # GUI CAMERA
        self.camera_gui.use()

        self.hud_sprites.draw()

        arcade.draw_text(f"SCORE {self.score}", 16, HEIGHT - 34, arcade.color.WHITE, 16)
        arcade.draw_text(f"BEST  {self.best_score}", 16, HEIGHT - 58, arcade.color.LIGHT_GRAY, 12)
        arcade.draw_text(f"SPEED {int(self.speed)}", WIDTH - 140, HEIGHT - 34, arcade.color.WHITE, 16)

        if self.game_over:
            self.overlay_sprites.draw()
            arcade.draw_text(
                "GAME OVER",
                WIDTH / 2,
                HEIGHT / 2 + 30,
                arcade.color.YELLOW,
                28,
                anchor_x="center",
            )
            arcade.draw_text(
                "Press R to Restart",
                WIDTH / 2,
                HEIGHT / 2 - 10,
                arcade.color.WHITE,
                16,
                anchor_x="center",
            )

    def on_update(self, delta_time):
        self.time += delta_time

        if self.game_over:
            self.shake_time = max(0.0, self.shake_time - delta_time)
            if self.shake_time <= 0:
                self.camera.position = (0, 0)
            return

        self.score += int(delta_time * 60)
        self.speed = min(900, self.speed + delta_time * 18)

        self.scroll += self.speed * delta_time * 0.35

        # Move stripes based on scroll
        for stripe in self.road_stripes:
            base_y = stripe.center_y
            # simple wrap
            stripe.center_y = ((base_y + self.scroll) % 120) - 120

        # Spawning
        self.spawn_timer += delta_time
        spawn_rate = max(0.18, 0.75 - self.score / 2500)
        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0
            for _ in range(random.randint(1, 4)):
                self.spawn_obstacle()

        # Smooth lane movement
        move_speed = 12
        target_x = LANES[self.target_lane]
        self.player.center_x += (target_x - self.player.center_x) * min(1, move_speed * delta_time)

        # Obstacles
        for obstacle in self.obstacles:
            obstacle.center_y += obstacle.change_y * delta_time

        for obstacle in self.obstacles[:]:
            if obstacle.top < -40:
                obstacle.remove_from_sprite_lists()

        if arcade.check_for_collision_with_list(self.player, self.obstacles):
            self.game_over = True
            self.best_score = max(self.best_score, self.score)
            self.shake_time = 0.25
            self.shake_power = 10

            # Build overlay sprite once
            overlay = arcade.SpriteSolidColor(WIDTH, HEIGHT, (0, 0, 0, 180))
            overlay.center_x = WIDTH // 2
            overlay.center_y = HEIGHT // 2
            self.overlay_sprites.append(overlay)

        # Camera shake
        if self.shake_time > 0:
            self.camera.position = (
                random.uniform(-self.shake_power, self.shake_power),
                random.uniform(-self.shake_power, self.shake_power),
            )
        else:
            self.camera.position = (0, 0)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.target_lane = max(0, self.target_lane - 1)
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.target_lane = min(NUM_LANES - 1, self.target_lane + 1)
        elif key == arcade.key.R and self.game_over:
            self.setup()


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    view = GameView()
    view.setup()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()
