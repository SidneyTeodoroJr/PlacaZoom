import flet as ft

def tile_clicked(e):
        print("Tile clicked")

ft.CupertinoListTile(
    additional_info=ft.Text("Wed Jan 24"),
    bgcolor_activated=ft.Colors.AMBER_ACCENT,
    leading=ft.Icon(name=ft.CupertinoIcons.GAME_CONTROLLER),
    title=ft.Text("CupertinoListTile: notched = False"),
    subtitle=ft.Text("Subtitle"),
    trailing=ft.Icon(name=ft.CupertinoIcons.ALARM),
    on_click=tile_clicked,
)