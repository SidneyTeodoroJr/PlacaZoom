import flet as ft
import threading
from back import yolo

def main(page: ft.Page):
    stop_flag = {"stop": False}
    image_display = ft.Image(
        src_base64="",
        width=430,
        height=932,
        fit=ft.ImageFit.CONTAIN,
        border_radius=ft.border_radius.all(20),
        expand=True
    )

    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT
    page.title = "PlacaZoom"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    def update_image(base64_data):
        image_display.src_base64 = base64_data
        page.update()

    def start_detection(e):
        stop_flag["stop"] = False
        threading.Thread(target=yolo, args=(update_image, stop_flag), daemon=True).start()

    def stop_detection(e):
        stop_flag["stop"] = True

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.PLAY_ARROW,
        on_click=start_detection
    )

    stop_button = ft.ElevatedButton("Parar Detecção", on_click=stop_detection)

    page.add(
        ft.Container(content=image_display, expand=True, bgcolor=ft.Colors.OUTLINE_VARIANT,),
        stop_button
    )

ft.app(target=main)
