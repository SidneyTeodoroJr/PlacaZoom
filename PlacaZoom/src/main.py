import threading
import asyncio
import base64
from os import makedirs
from os.path import expanduser, join

from cv2 import VideoCapture

from flet import (
    Page, Colors, IconButton, Icons, BottomAppBar,
    ImageFit, ImageRepeat, FloatingActionButtonLocation,
    Row, FloatingActionButton, CircleBorder, Offset, app,
    ThemeMode, MainAxisAlignment, CrossAxisAlignment, Image,
)

from back import process_image  # Importa do back-end

class AppState:
    def __init__(self):
        self.current_camera_index = 0
        self.cap = VideoCapture(self.current_camera_index)
        self.last_plate_text = None
        self.last_plate_crop_b64 = None
        self.last_plate_save_path = None

def main(page: Page):
    page.padding = 0
    page.window.center()
    page.title = "PlacaZoom"
    page.bgcolor = Colors.BLACK
    page.theme_mode = ThemeMode.LIGHT
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER

    state = AppState()

    def flip_camera(e):
        if state.cap.isOpened():
            state.cap.release()
        state.current_camera_index += 1
        new_cap = VideoCapture(state.current_camera_index)
        if not new_cap.isOpened():
            print(f"Camera {state.current_camera_index} unavailable. Returning to camera 0.")
            state.current_camera_index = 0
            new_cap = VideoCapture(state.current_camera_index)
        state.cap = new_cap
        print(f"Camera switched to {state.current_camera_index}.")

    def open_website(e):
        page.launch_url("https://github.com/SidneyTeodoroJr/PlacaZoom")

    def search_plate(e):
        if not state.last_plate_text or not state.last_plate_crop_b64:
            print("No detected plate to search.")
            return
        try:
            img_data = base64.b64decode(state.last_plate_crop_b64)
            pictures_path = join(expanduser("~"), "Pictures")
            makedirs(pictures_path, exist_ok=True)
            save_path = join(pictures_path, "car_license_plate.jpg")
            with open(save_path, "wb") as f:
                f.write(img_data)
            print(f"Cropped plate saved at {save_path}")
            state.last_plate_save_path = save_path
            image_plate.src = save_path
            image_plate.update()
        except Exception as ex:
            print(f"Error saving the plate image: {ex}")

        page.set_clipboard(state.last_plate_text)
        print(f"Plate text '{state.last_plate_text}' copied to clipboard.")
        page.launch_url("https://www.keplaca.com/")

    image_display = Image(
        expand=True,
        src="https://picsum.photos/600/600?grayscale",
        fit=ImageFit.FIT_HEIGHT,
        repeat=ImageRepeat.NO_REPEAT,
    )

    image_plate = Image(
        expand=True,
        src="https://picsum.photos/100/50?grayscale",
        fit=ImageFit.CONTAIN,
        repeat=ImageRepeat.NO_REPEAT,
        height=50,
        offset=Offset(0, -2.2),
    )

    page.bottom_appbar = BottomAppBar(
        bgcolor=Colors.BLACK,
        height=100,
        elevation=10,
        content=Row(
            controls=[
                IconButton(
                    icon=Icons.CAMERASWITCH_ROUNDED,
                    icon_color=Colors.WHITE,
                    on_click=flip_camera,
                    tooltip="Switch Camera",
                ),
                image_plate,
                IconButton(
                    icon=Icons.INFO_OUTLINE,
                    icon_color=Colors.WHITE,
                    tooltip="Information",
                    on_click=open_website
                ),
            ]
        ),
    )

    page.floating_action_button_location = FloatingActionButtonLocation.MINI_CENTER_DOCKED
    page.floating_action_button = FloatingActionButton(
        tooltip="Search plate",
        bgcolor=Colors.WHITE,
        icon=Icons.CAMERA_OUTLINED,
        shape=CircleBorder(),
        on_click=search_plate
    )

    page.add(image_display)

    async def camera_loop():
        while True:
            if not state.cap.isOpened():
                print("Camera not available.")
                await asyncio.sleep(1)
                continue

            ret, frame = state.cap.read()
            if not ret:
                print("Error capturing frame.")
                await asyncio.sleep(0.5)
                continue

            try:
                img_base64, plate_crop_b64, plate_text = process_image(frame)
                if img_base64:
                    image_display.src_base64 = img_base64
                    image_display.update()
                if plate_text and plate_crop_b64:
                    if plate_text != state.last_plate_text:
                        print(f"New plate detected: {plate_text}")
                    state.last_plate_text = plate_text
                    state.last_plate_crop_b64 = plate_crop_b64
                    try:
                        img_data = base64.b64decode(plate_crop_b64)
                        pictures_path = join(expanduser("~"), "Pictures")
                        makedirs(pictures_path, exist_ok=True)
                        save_path = join(pictures_path, "cropped_plate.jpg")
                        with open(save_path, "wb") as f:
                            f.write(img_data)
                        state.last_plate_save_path = save_path
                        image_plate.src = save_path
                        image_plate.update()
                    except Exception as ex:
                        print(f"Error saving/updating cropped image: {ex}")
            except Exception as e:
                print(f"Error processing image: {e}")

            await asyncio.sleep(0.1)

    def start_camera_loop():
        asyncio.run(camera_loop())

    threading.Thread(target=start_camera_loop, daemon=True).start()

app(main)