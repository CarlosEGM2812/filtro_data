import sys
import os
import flet as ft
import pyrebase
import datetime
import asyncio
import json
import requests

# ---------------------------
# Función para acceder a recursos empaquetados
# ---------------------------
def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, tanto en desarrollo como en ejecutable."""
    try:
        base_path = sys._MEIPASS  # cuando está empaquetado con PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------------------
# Configuración de Firebase para Pyrebase
# ---------------------------
firebase_config = {
    "apiKey": "AIzaSyBsprf32C7bBC1bK2GmPcpdyagyUvZ6mrU",
    "authDomain": "escaneosqr.firebaseapp.com",
    "databaseURL": "https://escaneosqr-default-rtdb.firebaseio.com",
    "projectId": "escaneosqr",
    "storageBucket": "escaneosqr.firebasestorage.app",
    "messagingSenderId": "868107728533",
    "appId": "1:868107728533:web:58ccc0f18a3883d61dcd9c",
    "measurementId": "G-N5X9QX2JWC"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# ---------------------------
# Función para verificar la conexión a Internet
# ---------------------------
def check_internet(timeout=3):
    """
    Verifica la conexión a Internet haciendo una petición HEAD a Google.
    Retorna True si hay conexión, False en caso contrario.
    """
    try:
        r = requests.head("https://www.google.com", timeout=timeout)
        return (r.status_code == 200)
    except:
        return False

# ---------------------------
# Tarea asíncrona para actualizar el ícono de conectividad
# ---------------------------
async def update_connectivity_status(page: ft.Page, connectivity_icon: ft.Icon):
    """
    Actualiza el ícono de conectividad cada 5 segundos.
    Muestra WIFI (azul) si hay conexión o WIFI_OFF (rojo) si no.
    """
    while True:
        online = check_internet()
        print("¿En línea?", online)  # Para depuración en consola
        if online:
            connectivity_icon.icon = ft.Icons.WIFI
            connectivity_icon.tooltip = "Conexión establecida"
            connectivity_icon.icon_color = "blue"
        else:
            connectivity_icon.icon = ft.Icons.WIFI_OFF
            connectivity_icon.tooltip = "Sin conexión a Internet"
            connectivity_icon.icon_color = "red"
        connectivity_icon.update()
        page.update()
        await asyncio.sleep(5)

# ---------------------------
# Tarea asíncrona para limpiar alertas
# ---------------------------
async def limpiar_alerta(alert_message: ft.Text, logo: ft.Image):
    """
    Limpia el mensaje de alerta y oculta el logo después de 7 segundos.
    """
    await asyncio.sleep(7)
    alert_message.value = ""
    alert_message.update()
    logo.visible = False
    logo.animate = ft.Animation(duration=500, curve=ft.AnimationCurve.EASE_IN_OUT)
    logo.update()

# ---------------------------
# Función para alternar temas (Dark/Light)
# ---------------------------
def toggle_theme(e, page: ft.Page, theme_button: ft.IconButton, appbar: ft.AppBar,
                 contenedor: ft.Container, dni_input: ft.TextField, buscar_btn: ft.ElevatedButton,
                 alert_container: ft.Container):
    """
    Alterna entre Dark y Light y actualiza los componentes con animaciones.
    """
    themes = {
        "Dark": {
            "bgcolor": "#0F2A19",
            "appbar_bg": "#1B5E20",
            "appbar_title_color": "#FFFFFF",
            "text_color": "#C8E6C9",
            "button_bg": "#2196F3",
            "input_bg": "#1B3D2F",
            "input_text": "#FFFFFF",
            "card_bg": "#1D2E25",
            "border_color": "#388E3C"
        },
        "Light": {
            "bgcolor": "#E8F5E9",
            "appbar_bg": "#43A047",
            "appbar_title_color": "#FFFFFF",
            "text_color": "#2E7D32",
            "button_bg": "#2196F3",
            "input_bg": "#C8E6C9",
            "input_text": "#1B5E20",
            "card_bg": "#FFFFFF",
            "border_color": "#388E3C"
        }
    }

    page.theme_mode = "Dark" if page.theme_mode == "Light" else "Light"
    colors = themes[page.theme_mode]

    page.bgcolor = colors["bgcolor"]
    appbar.bgcolor = colors["appbar_bg"]
    appbar.title.color = colors["appbar_title_color"]
    theme_button.icon = ft.Icons.DARK_MODE if page.theme_mode == "Dark" else ft.Icons.WB_SUNNY_OUTLINED
    theme_button.icon_color = colors["appbar_title_color"]
    theme_button.update()
    appbar.update()

    contenedor.animate = ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT)
    contenedor.bgcolor = colors["card_bg"]
    contenedor.border = ft.border.all(2, colors["border_color"])
    contenedor.update()

    dni_input.bgcolor = colors["input_bg"]
    dni_input.text_style = ft.TextStyle(color=colors["input_text"])
    dni_input.label_style = ft.TextStyle(color=colors["text_color"])
    dni_input.border_radius = 8
    dni_input.update()

    buscar_btn.style = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=colors["button_bg"],
        shape=ft.RoundedRectangleBorder(radius=8),
        overlay_color=ft.Colors.WHITE10
    )
    buscar_btn.update()

    for comp in alert_container.content.controls:
        if hasattr(comp, "src"):
            comp.visible = False
            comp.update()
        if hasattr(comp, "value"):
            comp.value = ""
            comp.update()
    alert_container.update()
    page.update()

# ---------------------------
# Función para obtener usuarios (solo en línea)
# ---------------------------
def obtener_usuarios():
    """
    Obtiene la lista de usuarios desde Firebase (usando Pyrebase).
    Retorna (usuarios, True) si la lectura fue exitosa; de lo contrario, retorna (None, False).
    """
    try:
        usuarios = db.child("usuarios").get().val()
        return usuarios, True
    except Exception as e:
        print("Error al obtener datos de Firebase:", e)
        return None, False

# ---------------------------
# Función para verificar si una persona es huésped
# ---------------------------
def verificar_huesped(e, dni_input: ft.TextField, page: ft.Page, alert_message: ft.Text, logo: ft.Image):
    """
    Verifica si el DNI ingresado corresponde a un huésped activo.
    """
    dni = dni_input.value.strip()
    if not dni or len(dni) != 8:
        alert_message.value = "Ingrese un DNI válido de 8 dígitos."
        alert_message.color = "red"
        logo.src = resource_path("assets/error.png")
        logo.visible = True
        logo.animate = ft.Animation(duration=500, curve=ft.AnimationCurve.ELASTIC_OUT)
        alert_message.update()
        logo.update()
        dni_input.value = ""
        dni_input.update()
        page.run_task(limpiar_alerta, alert_message, logo)
        return

    usuarios, online = obtener_usuarios()
    if not online:
        alert_message.value = "No se pudo obtener datos en línea."
        alert_message.color = "red"
        alert_message.update()
        return

    if usuarios:
        for usuario in usuarios.values():
            if str(usuario.get("dni")) == dni:
                fecha_sal = usuario.get("fecha_sal")
                if fecha_sal:
                    fecha_sin_hora = fecha_sal.split()[0]
                    fecha_salida = datetime.datetime.strptime(fecha_sin_hora, "%Y-%m-%d").date()
                    fecha_actual = datetime.datetime.today().date()
                    if fecha_actual > fecha_salida:
                        alert_message.value = "Esta persona no es huésped."
                        alert_message.color = "red"
                        logo.src = resource_path("assets/no_huesped.png")
                        logo.visible = True
                        logo.animate = ft.Animation(duration=500, curve=ft.AnimationCurve.ELASTIC_OUT)
                        alert_message.update()
                        logo.update()
                        dni_input.value = ""
                        dni_input.update()
                        page.run_task(limpiar_alerta, alert_message, logo)
                        return
                alert_message.value = "Esta persona es huésped."
                alert_message.color = "green"
                logo.src = resource_path("assets/usuario.png")
                logo.visible = True
                logo.animate = ft.Animation(duration=500, curve=ft.AnimationCurve.ELASTIC_OUT)
                alert_message.update()
                logo.update()
                dni_input.value = ""
                dni_input.update()
                page.run_task(limpiar_alerta, alert_message, logo)
                return

    alert_message.value = "Esta persona no es huésped."
    alert_message.color = "red"
    logo.src = resource_path("assets/no_huesped.png")
    logo.visible = True
    logo.animate = ft.Animation(duration=500, curve=ft.AnimationCurve.ELASTIC_OUT)
    alert_message.update()
    logo.update()
    dni_input.value = ""
    dni_input.update()
    page.run_task(limpiar_alerta, alert_message, logo)

# ---------------------------
# Función principal que construye la UI
# ---------------------------
def main(page: ft.Page):
    """
    Construye la UI de la aplicación con Flet.
    """
    # Cambiar el ícono de la ventana a tu logo personalizado
    page.window_icon = resource_path("assets/mi_icono.ico")

    page.title = "Búsqueda de Huéspedes"
    page.theme_mode = "Light"
    page.bgcolor = "#E8F5E9"

    # Botón para alternar tema
    theme_button = ft.IconButton(
        icon=ft.Icons.WB_SUNNY_OUTLINED,
        icon_color="#FFFFFF"
    )

    # Ícono de conectividad (estado inicial: azul)
    connectivity_icon = ft.Icon(ft.Icons.WIFI, color="blue", tooltip="Conexión establecida")

    # AppBar
    appbar = ft.AppBar(
        title=ft.Text("Gestión de Huéspedes", color="#FFFFFF"),
        center_title=True,
        bgcolor="#43A047",
        actions=[theme_button, connectivity_icon]
    )
    page.appbar = appbar

    # Campo de texto para DNI
    dni_input = ft.TextField(
        label="Ingrese DNI",
        label_style=ft.TextStyle(color="#2E7D32"),
        width=300,
        text_align=ft.TextAlign.CENTER,
        bgcolor="#C8E6C9",
        text_style=ft.TextStyle(color="#1B5E20"),
        border_radius=8
    )
    dni_input.on_change = lambda e: setattr(
        dni_input,
        "helper_text",
        "El DNI debe tener 8 dígitos." if len(dni_input.value.strip()) != 8 else ""
    )

    # Botón Buscar
    buscar_btn = ft.ElevatedButton(
        text="Buscar",
        on_click=lambda e: verificar_huesped(e, dni_input, page, alert_message, logo),
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor="#2196F3",
            shape=ft.RoundedRectangleBorder(radius=8),
            overlay_color=ft.Colors.WHITE10
        )
    )

    # Contenedor del filtro (campo DNI + botón)
    filtro_column = ft.Column(
        [dni_input, ft.Row([buscar_btn], alignment=ft.MainAxisAlignment.CENTER)],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20
    )

    # Contenedor principal
    contenedor = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SEARCH, size=30, color="#2E7D32"),
                        ft.Text("Buscador de Huéspedes", size=22, weight=ft.FontWeight.BOLD, color="#2E7D32")
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                filtro_column
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        alignment=ft.alignment.center,
        padding=20,
        border_radius=12,
        bgcolor="#FFFFFF",
        border=ft.border.all(2, "#388E3C"),
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(2, 4))
    )

    # Contenedor para logo y mensaje de alerta
    logo = ft.Image(src=resource_path("assets/placeholder.png"), width=250, height=250)
    logo.visible = False
    alert_message = ft.Text("", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    alerta_column = ft.Column(
        [logo, alert_message],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10
    )
    alert_container = ft.Container(content=alerta_column, alignment=ft.alignment.center, padding=10)

    page.add(contenedor, alert_container)

    theme_button.on_click = lambda e: toggle_theme(e, page, theme_button, appbar, contenedor, dni_input, buscar_btn, alert_container)
    page.update()

    # Inicia la tarea para actualizar el estado de conectividad
    page.run_task(update_connectivity_status, page, connectivity_icon)

if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="assets",
        view=ft.WEB_BROWSER
    )
