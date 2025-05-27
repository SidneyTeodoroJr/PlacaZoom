import cv2
import asyncio
import base64
import os
import httpx
import threading
import flet as ft

API_URL = "http://127.0.0.1:8000/detect"

class AppState:
    def __init__(self):
        self.current_camera_index = 0
        self.cap = cv2.VideoCapture(self.current_camera_index)
        self.last_plate_text = None
        self.last_plate_crop_b64 = None
        self.last_plate_save_path = None  # Novo: caminho do arquivo salvo

def main(page: ft.Page):
    page.padding = 0
    page.title = "PlacaZoom"
    page.bgcolor = ft.Colors.BLACK
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    state = AppState()

    def flip_camera(e):
        if state.cap.isOpened():
            state.cap.release()

        state.current_camera_index += 1
        new_cap = cv2.VideoCapture(state.current_camera_index)
        if not new_cap.isOpened():
            print(f"Câmera {state.current_camera_index} indisponível. Voltando para câmera 0.")
            state.current_camera_index = 0
            new_cap = cv2.VideoCapture(state.current_camera_index)
        state.cap = new_cap
        print(f"Câmera alterada para {state.current_camera_index}.")

    def open_website(e):
        page.launch_url("https://github.com/SidneyTeodoroJr/PlacaZoom")

    def search_plate(e):
        if not state.last_plate_text or not state.last_plate_crop_b64:
            print("Nenhuma placa detectada para pesquisar.")
            return

        try:
            img_data = base64.b64decode(state.last_plate_crop_b64)
            pictures_path = os.path.join(os.path.expanduser("~"), "Pictures")
            os.makedirs(pictures_path, exist_ok=True)
            save_path = os.path.join(pictures_path, "car_license_plate.jpg")
            with open(save_path, "wb") as f:
                f.write(img_data)
            print(f"Placa recortada salva em {save_path}")

            state.last_plate_save_path = save_path

            # Atualiza a imagem exibida da placa via arquivo salvo
            image_plate.src = save_path
            image_plate.update()

        except Exception as ex:
            print(f"Erro ao salvar a imagem da placa: {ex}")

        page.set_clipboard(state.last_plate_text)
        print(f"Texto da placa '{state.last_plate_text}' copiado para a área de transferência.")

        # Alterado: novo site para consulta
        page.launch_url("https://www.keplaca.com/")

    image_display = ft.Image(
        expand=True,
        src="https://picsum.photos/600/600?grayscale",
        fit=ft.ImageFit.FIT_HEIGHT,
        repeat=ft.ImageRepeat.NO_REPEAT,
    )

    image_plate = ft.Image(
        expand=True,
        src="https://picsum.photos/100/50?grayscale",  # Padrão inicial
        fit=ft.ImageFit.CONTAIN,
        repeat=ft.ImageRepeat.NO_REPEAT,
        height=50,
        offset=ft.Offset(0, -2.2),
    )

    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=ft.Colors.BLACK,
        height=100,
        elevation=10,
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CAMERASWITCH_ROUNDED,
                    icon_color=ft.Colors.WHITE,
                    on_click=flip_camera,
                    tooltip="Mudar Câmera",
                ),
                
                image_plate,

                ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Informações",
                    on_click=open_website
                ),
            ]
        ),
    )

    page.floating_action_button_location = ft.FloatingActionButtonLocation.MINI_CENTER_DOCKED
    page.floating_action_button = ft.FloatingActionButton(
        tooltip="Pesquisar placa",
        bgcolor=ft.Colors.WHITE,
        icon=ft.Icons.IMAGE_SEARCH,
        shape=ft.CircleBorder(),
        on_click=search_plate
    )

    page.add(image_display)

    async def camera_loop():
        async with httpx.AsyncClient(timeout=10) as client:
            while True:
                if not state.cap.isOpened():
                    print("Câmera não disponível.")
                    await asyncio.sleep(1)
                    continue

                ret, frame = state.cap.read()
                if not ret:
                    print("Erro ao capturar frame.")
                    await asyncio.sleep(0.5)
                    continue

                _, img_encoded = cv2.imencode('.jpg', frame)
                img_bytes = img_encoded.tobytes()
                files = {'file': ('frame.jpg', img_bytes, 'image/jpeg')}

                try:
                    response = await client.post(API_URL, files=files)
                    if response.status_code == 200:
                        data = response.json()
                        img_base64 = data.get('image_base64')
                        plate_text = data.get('plate_text')
                        plate_crop_b64 = data.get('plate_crop_base64')

                        if img_base64:
                            image_display.src_base64 = img_base64
                            image_display.update()

                        if plate_text and plate_crop_b64:
                            if plate_text != state.last_plate_text:
                                print(f"Nova placa detectada: {plate_text}")
                            state.last_plate_text = plate_text
                            state.last_plate_crop_b64 = plate_crop_b64

                            # Salva automaticamente a imagem e atualiza o image_plate
                            try:
                                img_data = base64.b64decode(plate_crop_b64)
                                pictures_path = os.path.join(os.path.expanduser("~"), "Pictures")
                                os.makedirs(pictures_path, exist_ok=True)
                                save_path = os.path.join(pictures_path, "placa_recortada.jpg")
                                with open(save_path, "wb") as f:
                                    f.write(img_data)
                                state.last_plate_save_path = save_path

                                image_plate.src = save_path
                                image_plate.update()

                            except Exception as ex:
                                print(f"Erro ao salvar/atualizar imagem recortada: {ex}")

                    else:
                        print(f"Resposta da API: {response.status_code}")
                except Exception as e:
                    print(f"Erro ao chamar API: {e}")

                await asyncio.sleep(0.1)

    def start_camera_loop():
        asyncio.run(camera_loop())

    threading.Thread(target=start_camera_loop, daemon=True).start()

ft.app(main)