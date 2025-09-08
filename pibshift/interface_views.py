import flet as ft
from core_logic import ler_planilha, gerar_rascunho, verificar_conflitos
from export_manager import exportar_pdf, exportar_ics, copiar_whatsapp
import json
import pandas as pd

def GerarEscalaView(page, navigate_to):

    def on_file_picker_result(e: ft.FilePickerResultEvent):
        if e.files:
            file_path.value = e.files[0].path
            page.update()

    def processar_rascunho(e):
        if not file_path.value:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione um arquivo de escala."), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        df, error = ler_planilha(file_path.value)
        if error:
            page.snack_bar = ft.SnackBar(ft.Text(error), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        rascunho, available_servers, error = gerar_rascunho(df)
        if error:
            page.snack_bar = ft.SnackBar(ft.Text(error), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return
        
        # Armazenar o rascunho e os servidores disponíveis para a próxima tela
        page.client_storage.set("rascunho_escala", json.dumps(rascunho))
        page.client_storage.set("available_servers", json.dumps(available_servers))

        page.snack_bar = ft.SnackBar(ft.Text("Rascunho criado com base na disponibilidade da planilha."))
        page.snack_bar.open = True
        navigate_to(1) # Navega para a tela de Edição
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_picker_result)
    page.overlay.append(file_picker)

    file_path = ft.TextField(label="Arquivo de entrada (.xlsx)", read_only=True, expand=True)

    return ft.Column(
        [
            ft.Row(
                [
                    file_path,
                    ft.ElevatedButton(
                        "Selecionar Planilha",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files(allowed_extensions=["xlsx"])
                    )
                ]
            ),
            ft.ElevatedButton(
                "Processar e Criar Rascunho",
                on_click=processar_rascunho
            )
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

def EditarEscalaView(page):

    rascunho_str = page.client_storage.get("rascunho_escala")
    rascunho = json.loads(rascunho_str) if rascunho_str else []
    available_servers_str = page.client_storage.get("available_servers")
    available_servers = json.loads(available_servers_str) if available_servers_str else {}

    def get_escala_atual_df():
        escala_data = []
        for row in data_table.rows:
            escala_data.append({
                "Data": row.cells[0].content.value,
                "Função": row.cells[1].content.value,
                "Voluntário": row.cells[2].content.value
            })
        return pd.DataFrame(escala_data)

    def on_dropdown_change(e):
        escala_df = get_escala_atual_df()
        conflitos = verificar_conflitos(escala_df)
        update_status_icons(conflitos)
        page.update()

    def update_status_icons(conflitos):
        for row in data_table.rows:
            data = row.cells[0].content.value
            voluntario = row.cells[2].content.value
            if data in conflitos and voluntario in conflitos[data]:
                row.cells[3].content = ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER)
            elif voluntario == "Não designado":
                row.cells[3].content = ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED)
            else:
                row.cells[3].content = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN)

    columns = [
        ft.DataColumn(ft.Text("Data")),
        ft.DataColumn(ft.Text("Função")),
        ft.DataColumn(ft.Text("Voluntário")),
        ft.DataColumn(ft.Text("Status")),
    ]

    rows = []
    for item in rascunho:
        data = item['Data']
        for area, voluntarios in item.items():
            if area != 'Data':
                # Lógica para determinar o status
                status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN)
                if "Não designado" in voluntarios:
                    status_icon = ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED)
                
                # Get available volunteers for this specific day and area
                day_servers = available_servers.get(data, {})
                area_servers = day_servers.get(area, [])
                
                dropdown_options = [ft.dropdown.Option(v) for v in area_servers]
                # Add the currently assigned volunteer if not in the list
                if voluntarios not in area_servers:
                    dropdown_options.append(ft.dropdown.Option(voluntarios))

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(data)),
                            ft.DataCell(ft.Text(area)),
                            ft.DataCell(ft.Dropdown(options=dropdown_options, value=voluntarios, on_change=on_dropdown_change)),
                            ft.DataCell(status_icon)
                        ]
                    )
                )

    data_table = ft.DataTable(columns=columns, rows=rows)

    def get_escala_final():
        escala_final = []
        for row in data_table.rows:
            escala_final.append({
                "Data": row.cells[0].content.value,
                "Função": row.cells[1].content.value,
                "Voluntário": row.cells[2].content.value
            })
        return pd.DataFrame(escala_final)

    def on_export_pdf(e):
        escala_df = get_escala_final()
        # Adicionar seletor de arquivo para salvar
        def on_save_file(e: ft.FilePickerResultEvent):
            if e.path:
                success, message = exportar_pdf(escala_df, e.path)
                if success:
                    page.snack_bar = ft.SnackBar(ft.Text(message))
                else:
                    page.snack_bar = ft.SnackBar(ft.Text(message, bgcolor=ft.Colors.RED))
                page.snack_bar.open = True
                page.update()
        
        file_picker = ft.FilePicker(on_result=on_save_file)
        page.overlay.append(file_picker)
        file_picker.save_file(allowed_extensions=["pdf"])

    def on_export_ics(e):
        escala_df = get_escala_final()
        def on_save_file(e: ft.FilePickerResultEvent):
            if e.path:
                success, message = exportar_ics(escala_df, e.path)
                if success:
                    page.snack_bar = ft.SnackBar(ft.Text(message))
                else:
                    page.snack_bar = ft.SnackBar(ft.Text(message, bgcolor=ft.Colors.RED))
                page.snack_bar.open = True
                page.update()
        
        file_picker = ft.FilePicker(on_result=on_save_file)
        page.overlay.append(file_picker)
        file_picker.save_file(allowed_extensions=["ics"])

    def on_copy_whatsapp(e):
        escala_df = get_escala_final()
        whatsapp_text = copiar_whatsapp(escala_df)
        page.set_clipboard(whatsapp_text)
        page.snack_bar = ft.SnackBar(ft.Text("Escala copiada para a área de transferência!"))
        page.snack_bar.open = True
        page.update()

    def confirmar_escala(e):
        # Lógica para confirmar a escala
        page.snack_bar = ft.SnackBar(ft.Text("Escala confirmada! Opções de exportação liberadas."))
        page.snack_bar.open = True
        export_section.visible = True
        data_table.disabled = True
        page.update()

    def editar_novamente(e):
        data_table.disabled = False
        export_section.visible = False
        page.snack_bar = ft.SnackBar(ft.Text("Escala em modo de rascunho."))
        page.snack_bar.open = True
        page.update()

    export_section = ft.Column(
        [
            ft.ElevatedButton("Exportar para PDF", on_click=on_export_pdf),
            ft.ElevatedButton("Gerar Convite .ics", on_click=on_export_ics),
            ft.ElevatedButton("Copiar Escala para WhatsApp", on_click=on_copy_whatsapp),
            ft.ElevatedButton("Editar Novamente", on_click=editar_novamente),
        ],
        visible=False,
        spacing=10,
        alignment=ft.MainAxisAlignment.CENTER
    )

    return ft.Column(
        [
            ft.Text("Editar Escala", size=20),
            data_table,
            ft.ElevatedButton("Confirmar Escala", on_click=confirmar_escala, bgcolor=ft.Colors.AMBER),
            export_section
        ],
        expand=True,
        scroll=ft.ScrollMode.ALWAYS
    )

def ConfiguracoesView(page):

    def on_theme_change(e):
        page.theme_mode = e.control.value
        save_settings()
        page.update()

    def get_save_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            save_dir_path_field.value = e.path
            save_settings()
            page.update()

    def save_settings():
        settings = {
            "theme_mode": page.theme_mode,
            "default_save_directory": save_dir_path_field.value
        }
        page.client_storage.set("pibshift.settings", json.dumps(settings))
        page.snack_bar = ft.SnackBar(ft.Text("Configurações salvas!"))
        page.snack_bar.open = True
        page.update()

    theme_switch = ft.Switch(label="Modo Escuro", on_change=on_theme_change)
    save_dir_picker = ft.FilePicker(on_result=get_save_directory_result)
    page.overlay.append(save_dir_picker)
    save_dir_path_field = ft.TextField(label="Diretório de Exportação Padrão", read_only=True, expand=True)

    # Carregar configurações salvas
    try:
        settings_str = page.client_storage.get("pibshift.settings")
        if settings_str:
            settings = json.loads(settings_str)
            page.theme_mode = settings.get("theme_mode", ft.ThemeMode.LIGHT)
            theme_switch.value = page.theme_mode == ft.ThemeMode.DARK
            save_dir_path_field.value = settings.get("default_save_directory", "")
    except (json.JSONDecodeError, TypeError):
        # Se houver erro ao carregar, usa os padrões
        pass

    return ft.Column(
        [
            ft.Text("Configurações", size=20),
            theme_switch,
            ft.Row(
                [
                    save_dir_path_field,
                    ft.ElevatedButton(
                        "Selecionar Diretório",
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda _: save_dir_picker.get_directory_path()
                    )
                ]
            ),
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )