import re
import flet as ft
import pandas as pd
import json
import os
import datetime
from collections import Counter

def extrair_nome_sobrenome(nome_completo):
    """
    Extrai o primeiro e o último nome de um nome completo.
    Se houver apenas um nome, retorna o próprio nome.
    Também reconhece apelidos para nomes específicos.
    """
    nome_lower = nome_completo.lower().strip()

    # Mapeamento de apelidos para nomes padronizados
    apelidos_para_nomes = {
        "gb marques": "Gabriel Marques",
        "lay": "Laysa",
        "layy": "Laysa",
    }

    # Verifica se o nome completo (em minúsculas) ou uma parte corresponde a um apelido
    for apelido, nome_padronizado in apelidos_para_nomes.items():
        if apelido in nome_lower:
            return nome_padronizado

    # Lógica original para extrair primeiro e último nome
    partes = nome_completo.split()
    return " ".join([partes[0], partes[-1]]) if len(partes) > 1 else partes[0]


def verifica_dias_consecutivos(escala, nome, data):
    """
    Verifica se um servidor trabalhará 3 ou mais dias consecutivos, incluindo a data atual.
    Retorna False se houver 3 ou mais dias consecutivos, True caso contrário.
    """
    dias_sequenciais = []
    for dia in escala:
        # Adicionado para garantir que dia é um dicionário e o valor é uma string
        if isinstance(dia, dict):
            for val in dia.values():
                if isinstance(val, str) and nome in val:
                    dias_sequenciais.append(dia.get('Data'))
                    break # Evita adicionar a mesma data múltiplas vezes

    dias_sequenciais.append(data)
    dias_sequenciais.sort()

    # Convertendo a lista para datetime objects para fácil comparação
    datas_dt = []
    # Usar um ano fixo (ex: 2000) para permitir a comparação de dias, ignorando o ano real
    fixed_year = 2000
    for dt_str in dias_sequenciais:
        if not dt_str: continue
        # Usar regex para encontrar o padrão DD/MM na string
        match = re.search(r'\b(\d{1,2}/\d{1,2})\b', dt_str)
        if match:
            date_part = match.group(1)
            try:
                # Adicionar o ano fixo e parsear
                full_date_str = f"{date_part}/{fixed_year}"
                datas_dt.append(datetime.datetime.strptime(full_date_str, '%d/%m/%Y').date())
            except ValueError:
                pass
        else:
            pass

    datas_dt.sort()

    count = 0
    for i in range(1, len(datas_dt)):
        if (datas_dt[i] - datas_dt[i-1]).days == 1:
            count += 1
        else:
            count = 0
        if count >= 3:
            return False
    return True


def run_escala(filepath, output_filename, selected_areas, generate_multiple_sheets=True):
    if not filepath:
        return False, "Por favor, selecione um arquivo de escala."

    try:
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.upper().str.strip()
    except FileNotFoundError:
        return False, "Arquivo não encontrado. Verifique o caminho do arquivo."
    except Exception as e:
        return False, f"Erro ao ler o arquivo: {e}"

    if 'ÁREA DE ATUAÇÃO' not in df.columns:
        return False, "A coluna 'ÁREA DE ATUAÇÃO' não foi encontrada."
    
    num_servidores_por_area = {
        'PRODUÇÃO': 1,
        'FILMAGEM': 3,
        'PROJEÇÃO': 1,
        'TAKE': 2,
    }

    shifts_count = {}
    max_shifts_per_person = 2
    priority_pair = ("Laysa", "Gabriel Marques")
    laysa_name, gabriel_name = priority_pair
    excluded_pair = ("Laysa", "Gabriel Nevile")

    colunas_datas = [col for col in df.columns if col not in ['CARIMBO DE DATA/HORA', 'ENDEREÇO DE E-MAIL', 'CELULAR (WHATSAPP)', 'NOME', 'ÁREA DE ATUAÇÃO']]
    
    escala_final = []

    for coluna in colunas_datas:
        dia_df = df[df[coluna] == 'SIM']
        alocacao_dia = {'Data': coluna}
        
        daily_available_servers = {}
        for area_key in num_servidores_por_area.keys():
            servidores_disponiveis_raw_nomes = dia_df[dia_df['ÁREA DE ATUAÇÃO'].str.contains(area_key, case=False)]['NOME'].tolist()
            current_area_available = []
            for nome_servidor in servidores_disponiveis_raw_nomes:
                nome_normalizado = extrair_nome_sobrenome(nome_servidor)
                if shifts_count.get(nome_normalizado, 0) < max_shifts_per_person and \
                   verifica_dias_consecutivos(escala_final, nome_normalizado, coluna):
                    current_area_available.append(nome_normalizado)
            daily_available_servers[area_key] = current_area_available

        if laysa_name in [s for sublist in daily_available_servers.values() for s in sublist]:
            for area_key in daily_available_servers:
                if excluded_pair[1] in daily_available_servers[area_key]:
                    daily_available_servers[area_key].remove(excluded_pair[1])
        elif excluded_pair[1] in [s for sublist in daily_available_servers.values() for s in sublist]:
            for area_key in daily_available_servers:
                if laysa_name in daily_available_servers[area_key]:
                    daily_available_servers[area_key].remove(laysa_name)

        allocated_for_day = set()
        temp_alocacao = {}

        laysa_can_be_filmag_cross = laysa_name in daily_available_servers.get('FILMAGEM', [])
        gabriel_can_be_prod_cross = gabriel_name in daily_available_servers.get('PRODUÇÃO', [])
        
        if laysa_can_be_filmag_cross and gabriel_can_be_prod_cross:
            temp_alocacao['FILMAGEM'] = [laysa_name]
            allocated_for_day.add(laysa_name)
            
            temp_alocacao['PRODUÇÃO'] = [gabriel_name]
            allocated_for_day.add(gabriel_name)

        for area, num_servidores in num_servidores_por_area.items():
            alocados = temp_alocacao.get(area, [])
            num_to_fill = num_servidores - len(alocados)

            if num_to_fill > 0:
                pool_disponivel = [s for s in daily_available_servers.get(area, []) if s not in allocated_for_day]
                novos_alocados = pool_disponivel[:num_to_fill]
                alocados.extend(novos_alocados)
                allocated_for_day.update(novos_alocados)
            
            temp_alocacao[area] = alocados

        for area, nomes in temp_alocacao.items():
            num_needed = num_servidores_por_area[area]
            if len(nomes) < num_needed:
                nomes.extend(['Não designado'] * (num_needed - len(nomes)))
            alocacao_dia[area] = '\n'.join(nomes)

        for nome in allocated_for_day:
            shifts_count[nome] = shifts_count.get(nome, 0) + 1

        escala_final.append(alocacao_dia)

    try:
        with pd.ExcelWriter(output_filename, engine='xlsxwriter') as writer:
            all_data = []
            for dia_escala in escala_final:
                row = {'Data': dia_escala.get('Data', '')}
                for area in selected_areas:
                    row[area] = dia_escala.get(area, 'Não designado')
                all_data.append(row)
            
            df_final = pd.DataFrame(all_data)
            if selected_areas:
                df_final = df_final[['Data'] + selected_areas]
            
            df_final.to_excel(writer, sheet_name="Escala Completa", index=False)

        return True, f"Escala criada e salva como '{output_filename}'"
    except Exception as e:
        return False, f"Erro ao salvar o arquivo: {e}"


class EscalaAppFlet:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Pib Shift v.1.1"
        self.page.vertical_alignment = ft.CrossAxisAlignment.START
        self.page.window.width = 800
        self.page.window.height = 600
        
        icon_path = os.path.join(os.path.dirname(__file__), "piblogo.ico")
        self.page.window.icon = icon_path
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.dialog = None
        self.loaded_df = None # Para armazenar o DataFrame carregado
        self.pending_generation_data = None

        # --- Componentes da UI ---
        self.input_file_path = ft.TextField(label="Arquivo de entrada (Excel)", read_only=True, expand=True)
        self.output_file_name = ft.TextField(
            label="Nome do arquivo de saída", 
            value="Escala_Final.xlsx", 
            expand=True,
            on_change=self.validar_nome_digitado,
            visible=False
        )
        self.area_checkboxes = [
            ft.Checkbox(label="PRODUÇÃO", value=True, data="PRODUÇÃO"),
            ft.Checkbox(label="FILMAGEM", value=True, data="FILMAGEM"),
            ft.Checkbox(label="PROJEÇÃO", value=True, data="PROJEÇÃO"),
            ft.Checkbox(label="TAKE", value=True, data="TAKE"),
        ]
        self.generate_multiple_sheets_switch = ft.Switch(
            label="Gerar Abas Separadas por Área",
            value=True,
            on_change=self.save_settings
        )
        self.use_default_dir_checkbox = ft.Checkbox(
            label="Habilitar diretório padrão para salvar",
            value=False,
            on_change=self.on_use_default_dir_change
        )
        self.save_dir_path_field = ft.TextField(
            label="Diretório padrão para salvar escalas",
            read_only=True,
            value="",
            expand=True
        )
        self.theme_radio_group = ft.RadioGroup(
            content=ft.Column(
                [
                    ft.Radio(value=ft.ThemeMode.LIGHT.value, label="Claro"),
                    ft.Radio(value=ft.ThemeMode.DARK.value, label="Escuro"),
                ]
            ),
            on_change=self.on_theme_change,
            value=ft.ThemeMode.LIGHT.value,
        )

        # --- Seletores de Arquivo ---
        self.generate_input_picker = ft.FilePicker(on_result=self.on_generate_input_file_selected)
        self.view_input_picker = ft.FilePicker(on_result=self.on_view_input_file_selected)
        self.output_file_dialog = ft.FilePicker(on_result=self.on_save_file_picked_for_generation)
        self.save_dir_dialog = ft.FilePicker(on_result=self.get_save_directory_result)
        self.page.overlay.extend([self.generate_input_picker, self.view_input_picker, self.output_file_dialog, self.save_dir_dialog])

        # --- Configurações e Estado ---
        self.load_settings()

        # --- Construção da UI ---
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Gerar Escala", content=self.create_generate_tab()),
                ft.Tab(text="Visualizar Escala", content=self.create_view_tab()),
                ft.Tab(text="Configurações", content=self.create_config_tab()),
            ],
            expand=1,
        )
        self.page.add(self.tabs)
        self.page.update()

    # --- Métodos de Construção de Abas ---
    def create_generate_tab(self):
        return ft.Column(
            [
                ft.Row(
                    [
                        self.input_file_path,
                        ft.ElevatedButton(
                            "Selecionar Arquivo de Entrada",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda _: self.generate_input_picker.pick_files(
                                allow_multiple=False,
                                allowed_extensions=["xlsx"]
                            ),
                        ),
                    ]
                ),
                self.output_file_name,
                ft.Text("Selecionar Áreas para Gerar:", size=16, weight=ft.FontWeight.BOLD),
                ft.Column(self.area_checkboxes),
                self.generate_multiple_sheets_switch,
                ft.Container(expand=True),
                ft.ElevatedButton("Gerar Escala", on_click=self.generate_escala)
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            expand=True,
        )

    def create_view_tab(self):
        self.search_field = ft.TextField(
            label="Pesquisar por evento, área ou nome...",
            expand=True,
            on_submit=self.filter_view
        )
        self.view_content = ft.Row(
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[ft.Text("Gere ou selecione um arquivo de escala para visualizar aqui.", style=ft.TextThemeStyle.HEADLINE_SMALL, text_align=ft.TextAlign.CENTER)]
        )

        return ft.Column(
            [
                ft.Row(
                    [
                        self.search_field,
                        ft.IconButton(
                            icon=ft.Icons.SEARCH,
                            tooltip="Pesquisar",
                            on_click=self.filter_view,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip="Abrir outro arquivo de escala",
                            on_click=lambda _: self.view_input_picker.pick_files(
                                allow_multiple=False,
                                allowed_extensions=["xlsx"]
                            ),
                        ),
                    ]
                ),
                ft.Divider(),
                self.view_content,
            ],
            expand=True,
        )

    def create_config_tab(self):
        return ft.Column(
            [
                ft.Text("Configurações", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Tema da Aplicação:"),
                self.theme_radio_group,
                ft.Divider(),
                ft.Text("Diretório Padrão para Salvar:"),
                self.use_default_dir_checkbox,
                ft.Row(
                    [
                        self.save_dir_path_field,
                        ft.ElevatedButton(
                            "Selecionar Diretório",
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=lambda _: self.save_dir_dialog.get_directory_path(),
                        ),
                    ]
                ),
                ft.ElevatedButton("Salvar Configurações", on_click=self.save_settings),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            expand=True,
        )

    # --- Handlers de Eventos ---
    def on_generate_input_file_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.input_file_path.value = e.files[0].path
            self.page.update()

    def on_view_input_file_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.load_and_display_excel(e.files[0].path)

    def on_save_file_picked_for_generation(self, e: ft.FilePickerResultEvent):
        if e.path:
            output_path = e.path if e.path.lower().endswith('.xlsx') else f"{e.path}.xlsx"
            
            if hasattr(self, 'pending_generation_data') and self.pending_generation_data:
                data = self.pending_generation_data
                success, message = run_escala(
                    data["input_path"],
                    output_path,
                    data["selected_areas"],
                    data["generate_multiple_sheets"]
                )

                if success:
                    self.mostrar_mensagem_sucesso(message)
                    self.load_and_display_excel(output_path)
                    self.tabs.selected_index = 1
                else:
                    self.mostrar_erro_nome_arquivo(message)
                
                self.pending_generation_data = None
        self.page.update()

    def get_save_directory_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.default_save_directory = e.path
            self.save_dir_path_field.value = e.path
            self.save_dir_path_field.update()
            self.save_settings()
        self.page.update()

    def on_use_default_dir_change(self, e):
        self.output_file_name.visible = e.control.value
        self.save_settings()
        self.page.update()

    def generate_escala(self, e):
        input_path = self.input_file_path.value
        if not input_path:
            self.mostrar_erro_nome_arquivo("Por favor, selecione um arquivo de entrada (Excel).")
            return

        selected_areas = [cb.data for cb in self.area_checkboxes if cb.value]
        if not selected_areas:
            self.mostrar_erro_nome_arquivo("Selecione pelo menos uma área para gerar a escala.")
            return

        use_default_dir = self.use_default_dir_checkbox.value and self.default_save_directory

        if use_default_dir:
            nome_arquivo = self.output_file_name.value
            is_valid, validation_message = self.validar_nome_arquivo(nome_arquivo)
            if not is_valid:
                self.mostrar_erro_nome_arquivo(validation_message)
                return
            
            output_path = os.path.join(self.default_save_directory, nome_arquivo)
            success, message = run_escala(input_path, output_path, selected_areas, self.generate_multiple_sheets_switch.value)
            if success:
                self.mostrar_mensagem_sucesso(message)
                self.load_and_display_excel(output_path)
                self.tabs.selected_index = 1
                self.page.update()
            else:
                self.mostrar_erro_nome_arquivo(message)
        else:
            self.pending_generation_data = {
                "input_path": input_path,
                "selected_areas": selected_areas,
                "generate_multiple_sheets": self.generate_multiple_sheets_switch.value
            }
            self.output_file_dialog.save_file(
                allowed_extensions=["xlsx"],
                file_name="Escala_Final.xlsx"
            )

    def load_and_display_excel(self, filepath):
        try:
            try:
                self.loaded_df = pd.read_excel(filepath, sheet_name='Escala Completa')
            except ValueError:
                self.loaded_df = pd.read_excel(filepath, sheet_name=0)

            self.loaded_df.fillna('', inplace=True)
            self.search_field.value = ""
            self.update_view(self.loaded_df)
        except Exception as e:
            self.mostrar_erro_nome_arquivo(f"Erro ao ler o arquivo: {e}")
            self.clear_view_tab()

    def filter_view(self, e):
        search_term = self.search_field.value.lower()
        if self.loaded_df is None: return

        if not search_term:
            self.update_view(self.loaded_df)
            return

        mask = self.loaded_df.apply(
            lambda row: row.astype(str).str.lower().str.contains(search_term, na=False).any(),
            axis=1
        )
        self.update_view(self.loaded_df[mask])

    def update_view(self, df_to_display):
        self.clear_view_tab()
        if df_to_display.empty:
            self.view_content.controls.append(ft.Text("Nenhum resultado encontrado."))
            self.page.update()
            return

        cards = []
        for index, row_data in df_to_display.iterrows():
            area_content = []
            for col_name, value in row_data.items():
                if col_name.upper() != 'DATA':
                    # Trata o valor para garantir que seja uma string e substitui \n por quebras de linha
                    names = str(value).replace('\\n', '\n')
                    area_content.append(
                        ft.ListTile(
                            title=ft.Text(col_name, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(names),
                        )
                    )
            
            card = ft.Card(
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text(f"Dia: {row_data.get('Data', 'Sem Data')}", style=ft.TextThemeStyle.HEADLINE_SMALL),
                        ft.Divider(),
                        *area_content
                    ])
                ),
                width=250,
                margin=ft.margin.only(right=10, top=5, bottom=5),
            )
            cards.append(card)

        self.view_content.controls.extend(cards)
        self.page.update()

    def clear_view_tab(self):
        self.view_content.controls.clear()
        self.page.update()

    # --- Métodos de Configuração ---
    def validar_nome_digitado(self, e):
        nome = e.control.value
        if nome:
            is_valid, validation_message = self.validar_nome_arquivo(nome)
            if not is_valid:
                e.control.error_text = validation_message
            else:
                e.control.error_text = None
            e.control.update()

    def validar_nome_arquivo(self, nome):
        caracteres_proibidos = r'[<>:"/\|?*\x00-\x1f]'
        nomes_reservados = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if re.search(caracteres_proibidos, nome):
            return False, f"Caracteres inválidos: {', '.join(set(re.findall(caracteres_proibidos, nome)))}"
        if nome.endswith('.') or nome.endswith(' '):
            return False, "Nome não pode terminar com ponto ou espaço"
        if len(nome) > 255: return False, "Nome muito longo"
        if nome.split('.')[0].upper() in nomes_reservados: return False, f'"{nome.split('.')[0].upper()}" é um nome reservado'
        return True, ""

    def mostrar_erro_nome_arquivo(self, mensagem):
        def fechar_dialogo(e):
            self.page.dialog.open = False
            self.page.update()

        self.page.dialog = ft.AlertDialog(modal=True, title=ft.Text("Erro"), content=ft.Text(mensagem), actions=[ft.TextButton("Entendi", on_click=fechar_dialogo)], actions_alignment=ft.MainAxisAlignment.END)
        self.page.dialog.open = True
        self.page.update()

    def mostrar_mensagem_sucesso(self, mensagem):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(mensagem), bgcolor=ft.Colors.GREEN_700)
        self.page.snack_bar.open = True
        self.page.update()

    def on_theme_change(self, e):
        self.page.theme_mode = ft.ThemeMode(e.control.value)
        self.save_settings()
        self.page.update()

    def save_settings(self, e=None):
        settings = {
            "theme_mode": self.page.theme_mode.value if self.page.theme_mode else ft.ThemeMode.LIGHT.value,
            "default_save_directory": self.default_save_directory,
            "generate_multiple_sheets": self.generate_multiple_sheets_switch.value,
            "use_default_directory": self.use_default_dir_checkbox.value
        }
        try:
            self.page.client_storage.set("escala_settings", json.dumps(settings))
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    def load_settings(self):
        self.default_save_directory = ""
        try:
            saved_settings_str = self.page.client_storage.get("escala_settings")
            if saved_settings_str:
                settings = json.loads(saved_settings_str)
                self.page.theme_mode = ft.ThemeMode(settings.get("theme_mode", ft.ThemeMode.LIGHT.value))
                self.default_save_directory = settings.get("default_save_directory", "")
                self.generate_multiple_sheets_switch.value = settings.get("generate_multiple_sheets", True)
                self.use_default_dir_checkbox.value = settings.get("use_default_directory", False)
                self.output_file_name.visible = self.use_default_dir_checkbox.value

                self.save_dir_path_field.value = self.default_save_directory
                self.theme_radio_group.value = self.page.theme_mode.value
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")

    def on_tab_change(self, e):
        if self.tabs.selected_index == 1 and self.loaded_df is not None:
             self.update_view(self.loaded_df)
        self.page.update()

def main(page: ft.Page):
    EscalaAppFlet(page)

if __name__ == "__main__":
    ft.app(target=main)