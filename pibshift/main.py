import flet as ft
from interface_views import GerarEscalaView, EditarEscalaView, ConfiguracoesView

def main(page: ft.Page):
    page.title = "PibShift 2.0"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START

    # Cores da identidade visual
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE_900, # #0D47A1
            secondary=ft.Colors.AMBER, # #FFC107
        )
    )
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE_GREY_800,
            secondary=ft.Colors.AMBER,
        )
    )

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

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        leading=ft.FloatingActionButton(icon=ft.Icons.CREATE, text="Nova Escala"),
        group_alignment=-0.9,
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
                label_content=ft.Text("Configurações"),
            ),
        ],
        on_change=change_view,
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
    main_content.controls.append(GerarEscalaView(page, navigate_to))
    page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
