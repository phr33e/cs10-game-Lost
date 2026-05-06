import arcade

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Simple Sprite Movement"
MOVEMENT_SPEED = 5

class MovementGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Variables that will hold sprite lists
        self.player_list = None
        self.player_sprite = None

    def setup(self):
        """ Set up the game and initialize the variables. """
        self.player_list = arcade.SpriteList()

        # THIS IS THE LINE WE CHANGED!
        # It looks for bill.jpg in your folder. The 0.3 shrinks the image so it fits the screen.
        self.player_sprite = arcade.Sprite("bill.jpg", 0.3)

        self.player_sprite.center_x = SCREEN_WIDTH // 2
        self.player_sprite.center_y = SCREEN_HEIGHT // 2

        self.player_list.append(self.player_sprite)

    def on_draw(self):
        """ Render the screen. """
        self.clear()
        self.player_list.draw()

    def on_update(self, delta_time):
        """ Movement and game logic """
        self.player_list.update()

        # --- Keep the player on the screen ---
        if self.player_sprite.left < 0:
            self.player_sprite.left = 0
        elif self.player_sprite.right > SCREEN_WIDTH - 1:
            self.player_sprite.right = SCREEN_WIDTH - 1

        if self.player_sprite.bottom < 0:
            self.player_sprite.bottom = 0
        elif self.player_sprite.top > SCREEN_HEIGHT - 1:
            self.player_sprite.top = SCREEN_HEIGHT - 1

    def on_key_press(self, key, modifiers):
        """ Called whenever a key is pressed. """
        if key == arcade.key.UP or key == arcade.key.W:
            self.player_sprite.change_y = MOVEMENT_SPEED
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.player_sprite.change_y = -MOVEMENT_SPEED
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """ Called when the user releases a key. """
        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.DOWN or key == arcade.key.S:
            self.player_sprite.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.A or key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

def main():
    window = MovementGame()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
