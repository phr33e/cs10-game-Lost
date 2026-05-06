import arcade
import base64
from io import BytesIO

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SCREEN_TITLE = "20 Lane Forward"
NUM_LANES = 20
LANE_WIDTH = SCREEN_WIDTH // NUM_LANES
SPEED = 90

IMAGE_B64 = """/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxAQEBAQEA8PEA8PDw8QDw8PDw8PDw8PFREWFhURExMYHSggGBolGxMTITEhJSkrLi4uFx8zODMtNygtLisBCgoKDg0OFxAQFy0dHR0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAWgDuwMBIgACEQEDEQH/xAAbAAEAAgMBAQAAAAAAAAAAAAAABQYBBAcDAv/EADkQAAIBAwMCBAQEBQMDBQAAAAECAwAEEQUSITFBBhMiUWEHFDKBkaGx8BRCUmJy4SNCU2KS0f/EABoBAAMBAQEBAAAAAAAAAAAAAAABAgMEBQb/xAAxEQACAgEDAwIEBQQDAAAAAAAAAQIRAwQSITFBBVFhEyJxgZGh8DJCUpHR4fH/2gAMAwEAAhEDEQA/APg..."""

class LaneGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.EERIE_BLACK)
        self.player_lane = 9
        self.background_offset = 0

        raw = base64.b64decode(IMAGE_B64)
        self.img_texture = arcade.Texture.load_from_image(BytesIO(raw), "subway-surfers-game-1.jpg")

        self.player = arcade.Sprite()
        self.player.texture = self.img_texture
        self.player.scale = 0.2
        self.player.center_y = 80

    def update_player_position(self):
        self.player.center_x = (self.player_lane * LANE_WIDTH) + (LANE_WIDTH / 2)

    def on_draw(self):
        self.clear()

        for i in range(1, NUM_LANES):
            x = i * LANE_WIDTH
            for y in range(-40, SCREEN_HEIGHT + 40, 40):
                arcade.draw_line(
                    x,
                    y + self.background_offset,
                    x,
                    y + 20 + self.background_offset,
                    arcade.color.DIM_GRAY,
                    1
                )

        self.player.draw()

    def on_update(self, delta_time):
        self.background_offset -= SPEED * delta_time
        if self.background_offset <= -40:
            self.background_offset += 40
        self.update_player_position()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT and self.player_lane > 0:
            self.player_lane -= 1
        elif key == arcade.key.RIGHT and self.player_lane < NUM_LANES - 1:
            self.player_lane += 1

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            lane = int(x // LANE_WIDTH)
            self.player_lane = max(0, min(NUM_LANES - 1, lane))


def main():
    LaneGame()
    arcade.run()


if __name__ == "__main__":
    main()
