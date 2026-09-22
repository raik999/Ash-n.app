import sys
import flet as ft

from app import main

if __name__ == "__main__":
    use_web = "--web" in sys.argv

    ft.app(
        target=main,
        assets_dir="assets",
        view=ft.AppView.WEB_BROWSER if use_web else ft.AppView.FLET_APP,
        port=8550 if use_web else 0,
    )
