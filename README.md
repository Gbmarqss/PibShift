Prompt Final: Desenvolvimento do Aplicativo PibShift 2.0
1. Título do Projeto

PibShift 2.0

2. Visão Geral e Objetivos

Modernizar a versão 1.1 do PibShift com UI em Flet, menu lateral e identidade visual da PIB de Madureira.

Escopo da 2.0: single-user, arquivos .xlsx como fonte, exportação controlada (PDF, ICS, WhatsApp).

Escopo futuro (v3.0): multiusuário, banco de dados, login etc.

A lógica validada na versão 1.1 deve ser importada e integrada ao módulo de lógica da 2.0.

3. Arquitetura Técnica e Estrutura de Arquivos
Estrutura recomendada:
/pibshift
│── main.py              # Ponto de entrada: inicializa Flet, define tema, monta NavigationRail, chama as views
│── interface_views.py   # Camada de UI: telas (Gerar Escala, Editar Escala, Configurações)
│── core_logic.py        # Camada de lógica: leitura do .xlsx, aplicação de regras, criação do rascunho, verificação de conflitos
│── utils.py             # Funções auxiliares (formatação de datas, validações, etc.)
│── export_manager.py    # Exportação: PDF (fpdf2/reportlab), ICS (ics), copiar texto formatado para WhatsApp
│── assets/              # Pasta de ícones, imagens, logos
│── data/                # Pasta para armazenar escalas geradas, rascunhos temporários, exportações

Função de cada módulo:

main.py

Define tema global (azul + dourado).

Inicializa a janela.

Configura ft.NavigationRail e troca de telas.

Chama funções de interface_views.

interface_views.py

Define as telas do app:

Tela Gerar Escala (carregar .xlsx e chamar core_logic.py).

Tela Editar Escala (renderiza ft.DataTable com dropdowns + status).

Tela Configurações (switch dark/light, diretórios, preferências).

core_logic.py

Importar/refatorar funções da versão 1.1:

ler_planilha() → usa pandas/openpyxl para transformar .xlsx em DataFrame.

gerar_rascunho() → monta escala inicial (voluntários × datas × áreas).

verificar_conflitos() → detecta voluntários duplicados ou em múltiplas áreas no mesmo dia.

atualizar_escala() → reflete edições feitas pelo usuário.

Retorna dados no formato adequado para renderização em ft.DataTable.

utils.py

Formatação de datas (dd/mm/aaaa → domingo manhã 12/05/2025).

Funções auxiliares de checagem de disponibilidade.

export_manager.py

exportar_pdf(escala)

exportar_ics(escala)

copiar_whatsapp(escala)

Garante que só exporta após a escala ser confirmada.

4. Identidade Visual

Azul institucional: #0D47A1 (base em ft.colors.BLUE_900).

Dourado/âmbar: #FFC107 (base em ft.colors.AMBER).

Tema aplicado globalmente em main.py.

Modo claro e escuro persistidos em local storage.

5. UI e UX Específicas
5.1 Navegação

Menu lateral fixo (ft.NavigationRail).

Ícones:

Gerar Escala → ft.icons.POST_ADD

Editar Escala → ft.icons.TABLE_VIEW

Configurações → ft.icons.SETTINGS_OUTLINED

5.2 Tela "Gerar Escala"

Passo 1: Selecionar planilha .xlsx (ft.FilePicker).

Passo 2: Botão "Processar e Criar Rascunho" → chama core_logic.py.

Exibe mensagem: "Rascunho criado com base na disponibilidade da planilha."

Navega automaticamente para Editar Escala.

5.3 Tela "Editar Escala"

Tabela de Escala (ft.DataTable):

Colunas: Data, Função, Voluntário (Dropdown), Status (ícone colorido).

Cores do status:

✅ Verde = ok

⚠️ Amarelo (ou dourado) = conflito

❌ Vermelho = vaga vazia

Fluxo de edição:

Escala começa como Rascunho.

Botão "Confirmar Escala" (dourado) → trava edição e libera exportação.

Ao editar novamente → volta automaticamente para rascunho.

Seção de Exportação (só aparece após confirmação):

"Exportar para PDF"

"Gerar Convite .ics"

"Copiar Escala para WhatsApp"

5.4 Tela "Configurações"

Switch claro/escuro (persistente).

Seleção de diretório de exportação.

Preferências salvas em local storage.

6. Regras Críticas

Importar e integrar a lógica da v1.1 em core_logic.py.

Não permitir exportação antes da confirmação da escala.

Escala editada após confirmação → volta automaticamente a rascunho.

Estrutura modular clara (main, views, core_logic, utils, export_manager).

UI responsiva (desktop prioridade, mas adaptável para tablet/celular).