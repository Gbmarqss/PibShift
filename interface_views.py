import flet as ft
from core_logic import ler_planilha, gerar_rascunho, verificar_conflitos
from export_manager import exportar_pdf, exportar_ics, exportar_xlsx, copiar_whatsapp
import json
import pandas as pd
import time
import threading

def GerarEscalaView(page, navigate_to):
    # Estado dos ministérios selecionados
    ministerios_selecionados = {
        'PRODUÇÃO': ft.Checkbox(value=True, label="Produção"),
        'FILMAGEM': ft.Checkbox(value=True, label="Filmagem"), 
        'PROJEÇÃO': ft.Checkbox(value=True, label="Projeção"),
        'TAKE': ft.Checkbox(value=True, label="Take"),
        'ILUMINAÇÃO': ft.Checkbox(value=True, label="Iluminação")
    }
    
    file_path = ft.TextField(
        label="Arquivo de entrada (.xlsx)", 
        read_only=True, 
        expand=True,
        hint_text="Selecione a planilha de disponibilidade"
    )
    
    escala_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    loading = ft.ProgressRing(visible=False)
    escala_df_global = None

    def get_button_bgcolor():
        return ft.Colors.BLUE_GREY_50 if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900

    def get_button_color():
        return ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.WHITE

    def on_file_picker_result(e: ft.FilePickerResultEvent):
        if e.files:
            file_path.value = e.files[0].path
            page.update()

    def mostrar_escala(df):
        nonlocal escala_df_global
        escala_df_global = df
        escala_container.controls.clear()
        
        if df.empty:
            escala_container.controls.append(ft.Text("Nenhuma escala encontrada", color=ft.Colors.GREY))
        else:
            for data, grupo in df.groupby('Data'):
                card_content = []
                card_content.append(ft.Text(f"📅 {data}", size=16, weight=ft.FontWeight.BOLD))
                card_content.append(ft.Divider())
                
                for _, row in grupo.iterrows():
                    funcao = row['Funcao'].split(' ')[0] if ' ' in row['Funcao'] else row['Funcao']
                    card_content.append(ft.Row([
                        ft.Text(funcao + ":", width=120, weight=ft.FontWeight.BOLD),
                        ft.Text(row['Voluntario'])
                    ]))
                
                escala_container.controls.append(ft.Card(
                    content=ft.Container(content=ft.Column(card_content), padding=15),
                    width=400
                ))
        
        page.update()

    def processar_para_edicao(e):
        nonlocal escala_df_global
        
        if not file_path.value:
            mostrar_erro("Por favor, selecione um arquivo de escala.")
            return

        loading.visible = True
        page.update()

        try:
            df, error = ler_planilha(file_path.value)
            if error:
                mostrar_erro(error)
                return

            ministerios_ativos = [k for k, v in ministerios_selecionados.items() if v.value]
            if not ministerios_ativos:
                mostrar_erro("Selecione pelo menos um ministério.")
                return

            rascunho, available_servers, error = gerar_rascunho(df, ministerios_ativos)
            if error:
                mostrar_erro(error)
                return
            
            page.client_storage.set("rascunho_escala", json.dumps(rascunho))
            page.client_storage.set("available_servers", json.dumps(available_servers))
            page.client_storage.set("ministerios_ativos", json.dumps(ministerios_ativos))

            navigate_to(1)
            
        except Exception as e:
            mostrar_erro(f"Erro inesperado: {str(e)}")
        finally:
            loading.visible = False
            page.update()

    def mostrar_erro(message):
        page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.RED)
        page.snack_bar.open = True
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_picker_result)
    page.overlay.append(file_picker)

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Gerar Nova Escala", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Ministérios:", weight=ft.FontWeight.BOLD),
                ft.Row([cb for cb in ministerios_selecionados.values()], wrap=True),
                ft.Row([
                    file_path,
                    ft.ElevatedButton(
                        "Selecionar Planilha",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files(allowed_extensions=["xlsx"]),
                        bgcolor=get_button_bgcolor(),
                        color=get_button_color()
                    )
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        "Gerar e Editar Escala",
                        icon=ft.Icons.EDIT,
                        on_click=processar_para_edicao,
                        bgcolor=get_button_bgcolor(),
                        color=get_button_color(),
                        expand=True
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=20,
            expand=True
        ),
        padding=20,
        expand=True
    )

def EditarEscalaView(page):
    rascunho_str = page.client_storage.get("rascunho_escala")
    rascunho_slots = json.loads(rascunho_str) if rascunho_str else []
    
    available_servers_str = page.client_storage.get("available_servers")
    available_servers = json.loads(available_servers_str) if available_servers_str else {}
    
    if not rascunho_slots:
        return ft.Column([
            ft.Text("Editar Escala", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Nenhum rascunho encontrado. Gere uma escala primeiro."),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    # CORES ADAPTATIVAS
    def get_alert_color():
        return ft.Colors.ORANGE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.AMBER
    
    def get_alert_bgcolor():
        return ft.Colors.ORANGE_50 if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.AMBER_900
    
    def get_card_bgcolor():
        return ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_900
    
    def get_text_color():
        return ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.WHITE

    def get_button_bgcolor():
        return ft.Colors.BLUE_GREY_50 if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900

    def get_button_color():
        return ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.WHITE

    search_field = ft.TextField(
        label="Buscar por data, função ou voluntário...",
        icon=ft.Icons.SEARCH,
        hint_text="Digite para filtrar a escala",
        expand=True
    )

    escala_por_dia = {}
    for slot in rascunho_slots:
        data = slot['Data']
        if data not in escala_por_dia:
            escala_por_dia[data] = []
        escala_por_dia[data].append(slot)

    dropdown_refs = {}
    
    # CONTAINER PRINCIPAL COM SCROLL
    cards_container = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    # CONTAINER RESPONSIVO
    responsive_container = ft.ResponsiveRow(
        spacing=15,
        run_spacing=15,
        expand=False
    )
    
    todos_os_cards = []
    cards_data = {}
    alertas_conflito = {}

    def filtrar_cards(e):
        termo_busca = e.control.value.lower().strip()
        responsive_container.controls.clear()
        
        if not termo_busca:
            for card in todos_os_cards:
                responsive_container.controls.append(card)
        else:
            cards_filtrados = []
            for card, card_info in cards_data.items():
                data_match = termo_busca in card_info['data'].lower()
                funcoes_match = any(termo_busca in funcao.lower() for funcao in card_info['funcoes'])
                voluntarios_match = any(termo_busca in voluntario.lower() for voluntario in card_info['voluntarios'])
                
                if data_match or funcoes_match or voluntarios_match:
                    cards_filtrados.append(card)
            
            for card in cards_filtrados:
                responsive_container.controls.append(card)
        
        page.update()

    search_field.on_change = filtrar_cards

    def get_voluntarios_disponiveis(data, area):
        if data in available_servers and area in available_servers[data]:
            return available_servers[data][area]
        return []

    def get_escala_atual_df():
        escala_data = []
        for data, slots in escala_por_dia.items():
            for slot in slots:
                dropdown_id = f"{data}_{slot['Funcao']}"
                if dropdown_id in dropdown_refs:
                    voluntario = dropdown_refs[dropdown_id].value
                    funcao = slot['Funcao']
                    
                    escala_data.append({
                        "Data": data,
                        "Funcao": funcao,
                        "Voluntario": voluntario
                    })
        
        if not escala_data:
            return pd.DataFrame(columns=['Data', 'Funcao', 'Voluntario'])

        return pd.DataFrame(escala_data)

    def verificar_conflitos_corrigido(escala_df):
        """Verificação de conflitos corrigida - só marca se estiver em múltiplas funções no MESMO dia"""
        conflitos = []
        
        # Agrupar por data e voluntário
        for data, grupo_data in escala_df.groupby('Data'):
            # Contar quantas funções cada voluntário tem nessa data específica
            contagem_voluntarios = grupo_data[grupo_data['Voluntario'] != 'Não designado'].groupby('Voluntario').size()
            
            # Verificar voluntários com mais de uma função no MESMO dia
            for voluntario, count in contagem_voluntarios.items():
                if count > 1:
                    conflitos.append((data, voluntario))
        
        return conflitos

    def verificar_e_mostrar_conflitos():
        try:
            escala_df = get_escala_atual_df()
            if 'Voluntario' not in escala_df.columns:
                escala_df['Voluntario'] = 'Não designado'

            # Usar a função corrigida
            conflitos = verificar_conflitos_corrigido(escala_df)
            
            # Limpar alertas anteriores
            for alerta in list(alertas_conflito.values()):
                if hasattr(alerta, 'parent') and alerta.parent and alerta in alerta.parent.controls:
                    alerta.parent.controls.remove(alerta)
            alertas_conflito.clear()

            # Remover cor de fundo de todos os dropdowns
            for dropdown in dropdown_refs.values():
                dropdown.bgcolor = None

            # Aplicar alertas apenas para conflitos reais
            for (data, voluntario) in conflitos:
                for dropdown_id, dropdown in dropdown_refs.items():
                    if data in dropdown_id and dropdown.value == voluntario:
                        parent_row = dropdown.parent
                        if parent_row and isinstance(parent_row, ft.Row):
                            if dropdown_id not in alertas_conflito:
                                alerta_icon = ft.Icon(
                                    ft.Icons.WARNING,
                                    color=get_alert_color(),
                                    size=20,
                                    tooltip=f"Conflito: {voluntario} está em múltiplas funções no dia {data}"
                                )
                                alertas_conflito[dropdown_id] = alerta_icon
                                if alerta_icon not in parent_row.controls:
                                    parent_row.controls.append(alerta_icon)
                        
                        # Aplicar cor de fundo apenas ao dropdown com conflito
                        if page.theme_mode == ft.ThemeMode.LIGHT:
                            dropdown.bgcolor = ft.Colors.ORANGE_100
                        else:
                            dropdown.bgcolor = ft.Colors.AMBER_800
            
            page.update()
        except Exception as e:
            print(f"Erro ao verificar conflitos: {e}")

    def on_dropdown_change(e):
        verificar_e_mostrar_conflitos()

    pdf_file_picker = ft.FilePicker(on_result=lambda e: on_save_result(e, 'pdf'))
    excel_file_picker = ft.FilePicker(on_result=lambda e: on_save_result(e, 'excel'))
    ics_file_picker = ft.FilePicker(on_result=lambda e: on_save_result(e, 'ics'))

    def on_save_result(e: ft.FilePickerResultEvent, tipo: str):
        if e.path:
            escala_df = get_escala_atual_df()
            
            if tipo == 'pdf':
                success, message = exportar_pdf(escala_df, e.path)
            elif tipo == 'excel':
                success, message = exportar_xlsx(escala_df, e.path)
            elif tipo == 'ics':
                success, message = exportar_ics(escala_df, e.path)

            if success:
                page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.GREEN)
            else:
                page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

    def exportar_whatsapp(e):
        escala_df = get_escala_atual_df()
        texto = copiar_whatsapp(escala_df)
        page.set_clipboard(texto)
        page.snack_bar = ft.SnackBar(
            ft.Text("Texto copiado para a área de transferência!"),
            bgcolor=ft.Colors.GREEN
        )
        page.snack_bar.open = True
        page.update()

    page.overlay.extend([pdf_file_picker, excel_file_picker, ics_file_picker])

    # Criar cards
    for data, slots in escala_por_dia.items():
        slot_controls = []
        funcoes_card = []
        voluntarios_card = []
        
        for slot in slots:
            dropdown_id = f"{data}_{slot['Funcao']}"
            funcao_display = slot['Funcao']
            
            area_base = funcao_display.split(' ')[0] if ' ' in funcao_display else funcao_display
            if area_base in ["Fotografo", "Suporte"]:
                area_base = "TAKE"
            
            voluntarios_disponiveis = get_voluntarios_disponiveis(data, area_base)
            
            opcoes_dropdown = [ft.dropdown.Option("Não designado")]
            for voluntario in sorted(list(set(voluntarios_disponiveis + [slot['Voluntario']]))):
                if voluntario != "Não designado":
                    opcoes_dropdown.append(ft.dropdown.Option(voluntario))
            
            # DROPDOWN CORRIGIDO - BORDAS ARREDONDADAS E RESPONSIVO
            dropdown = ft.Dropdown(
                value=slot['Voluntario'],
                options=opcoes_dropdown,
                on_change=on_dropdown_change,
                width=200,
                border_radius=8,  # BORDAS ARREDONDADAS
                border_color=ft.Colors.GREY_400,
                text_size=14,
                tooltip=f"Selecione um voluntário para {funcao_display}",
                content_padding=10,
            )
            dropdown_refs[dropdown_id] = dropdown
            
            funcoes_card.append(funcao_display.lower())
            voluntarios_card.append(slot['Voluntario'].lower())
            
            # LINHA RESPONSIVA - se adapta ao tamanho da tela
            linha = ft.ResponsiveRow([
                ft.Container(
                    ft.Text(funcao_display + ":", weight=ft.FontWeight.BOLD, color=get_text_color()),
                    col={"sm": 12, "md": 4},
                    padding=5
                ),
                ft.Container(
                    dropdown,
                    col={"sm": 12, "md": 8},
                    padding=5
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            slot_controls.append(linha)

        # Card individual
        card = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"📅 {data}", size=16, weight=ft.FontWeight.BOLD, color=get_text_color()),
                        ft.Divider(),
                        *slot_controls
                    ]),
                    padding=15,
                ),
                elevation=5,
                margin=10,
            ),
            col={"sm": 12, "md": 6, "lg": 4},
            padding=5
        )
        
        cards_data[card] = {
            'data': data.lower(),
            'funcoes': funcoes_card,
            'voluntarios': [v.lower() for v in voluntarios_card]
        }
        
        todos_os_cards.append(card)

    # Adicionar cards ao container
    for card in todos_os_cards:
        responsive_container.controls.append(card)

    cards_container.controls.append(responsive_container)

    def iniciar_verificacao():
        time.sleep(0.5)
        verificar_e_mostrar_conflitos()
    
    threading.Thread(target=iniciar_verificacao, daemon=True).start()

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Editar Escala", size=24, weight=ft.FontWeight.BOLD, color=get_text_color()),
                ft.Divider(),
                
                # Barra de busca
                ft.Container(
                    content=ft.Row([search_field], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(bottom=10)
                ),
                
                # Botões de exportação
                ft.ResponsiveRow([
                    ft.Container(
                        ft.ElevatedButton(
                            "📄 PDF", 
                            on_click=lambda e: pdf_file_picker.save_file(allowed_extensions=["pdf"], file_name="escala_pibshift.pdf"), 
                            bgcolor=get_button_bgcolor(), 
                            color=get_button_color(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        col={"sm": 6, "md": 3},
                        padding=5
                    ),
                    ft.Container(
                        ft.ElevatedButton(
                            "📊 Excel", 
                            on_click=lambda e: excel_file_picker.save_file(allowed_extensions=["xlsx"], file_name="escala_pibshift.xlsx"), 
                            bgcolor=get_button_bgcolor(), 
                            color=get_button_color(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        col={"sm": 6, "md": 3},
                        padding=5
                    ),
                    ft.Container(
                        ft.ElevatedButton(
                            "📅 ICS", 
                            on_click=lambda e: ics_file_picker.save_file(allowed_extensions=["ics"], file_name="escala_pibshift.ics"), 
                            bgcolor=get_button_bgcolor(), 
                            color=get_button_color(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        col={"sm": 6, "md": 3},
                        padding=5
                    ),
                    ft.Container(
                        ft.ElevatedButton(
                            "💬 WhatsApp", 
                            on_click=exportar_whatsapp, 
                            bgcolor=get_button_bgcolor(), 
                            color=get_button_color(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        col={"sm": 6, "md": 3},
                        padding=5
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                # Alerta de conflitos
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=get_alert_color(), size=16),
                        ft.Text("Ícone de alerta indica conflito: mesma pessoa em múltiplas funções no MESMO dia", 
                               size=12, color=get_text_color())
                    ]),
                    padding=10,
                    bgcolor=get_alert_bgcolor(),
                    border_radius=8,
                    margin=ft.margin.only(bottom=10)
                ),
                
                # Container dos cards
                ft.Container(
                    content=cards_container,
                    expand=True,
                )
            ],
            spacing=10,
            expand=True
        ),
        padding=10,
        expand=True
    )

def ConfiguracoesView(page):
    theme_switch = ft.Switch(label="Modo Escuro", value=page.theme_mode == ft.ThemeMode.DARK)
    
    def on_theme_change(e):
        page.theme_mode = ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        settings = {"theme_mode": page.theme_mode.value}
        page.client_storage.set("pibshift.settings", json.dumps(settings))
        page.update()

    theme_switch.on_change = on_theme_change

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Configurações", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                theme_switch,
            ],
            spacing=20
        ),
        padding=20,
        expand=True
    )