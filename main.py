import os
import sys
import flet as ft
from interface_views import GerarEscalaView, EditarEscalaView, ConfiguracoesView
import json

def main(page: ft.Page):
    page.title = "PibShift 2.0"
    
    page.window_icon = "favicon.ico" 
    
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START

    # Carregar configurações de tema
    try:
        settings_str = page.client_storage.get("pibshift.settings")
        if settings_str:
            settings = json.loads(settings_str)
            theme_value = settings.get("theme_mode", "light")
            page.theme_mode = ft.ThemeMode.DARK if theme_value == "dark" else ft.ThemeMode.LIGHT
        page.update()
    except:
        page.theme_mode = ft.ThemeMode.LIGHT

    def navigate_to(view_index):
        main_content.controls.clear()
        if view_index == 0:
            main_content.controls.append(GerarEscalaView(page, navigate_to))
        elif view_index == 1:
            main_content.controls.append(EditarEscalaView(page))
        elif view_index == 2:
            main_content.controls.append(ConfiguracoesView(page))
        rail.selected_index = view_index
        page.update()

    def change_view(e):
        navigate_to(e.control.selected_index)

    # Navigation Rail
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.POST_ADD,
                selected_icon=ft.Icons.POST_ADD_OUTLINED,
                label="Gerar Escala",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.TABLE_VIEW,
                selected_icon=ft.Icons.TABLE_VIEW_OUTLINED,
                label="Editar Escala",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Configurações",
            ),
        ],
        on_change=change_view,
    )

    def nova_escala_click(e):
        # Limpa o rascunho salvo
        page.client_storage.remove("rascunho_escala")
        page.client_storage.remove("available_servers")
        page.client_storage.remove("ministerios_ativos")
        # Navega para a tela de gerar escala
        navigate_to(0)

    # AppBar com botão Nova Escala
    page.appbar = ft.AppBar(
        title=ft.Text("PibShift"),
        actions=[
            ft.ElevatedButton(
                "Nova Escala", 
                icon=ft.Icons.ADD, 
                on_click=nova_escala_click,
                bgcolor=ft.Colors.BLUE_GREY_50 if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900,
                color=ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.WHITE
            )
        ]
    )

    main_content = ft.Column(alignment=ft.MainAxisAlignment.START, expand=True)

    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                main_content,
            ],
            expand=True,
        )
    )
    
    # Carrega a view inicial
    navigate_to(0)
    page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")