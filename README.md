# PibShift - Automação de Escalas de Voluntários

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Funcional-green?style=for-the-badge)

## 🎯 Sobre o Projeto

O **PibShift** é uma aplicação Desktop desenvolvida em Python para automatizar a gestão e criação de escalas de voluntários. O projeto nasceu da necessidade de otimizar um processo manual que consumia horas e gerava conflitos de agenda na organização de equipes ministeriais.

O software processa a disponibilidade dos voluntários (coletada via Google Forms/Excel), aplica regras de distribuição lógica para evitar conflitos e gera a escala final pronta para divulgação em múltiplos formatos.

## ✨ Principais Funcionalidades

* **Processamento Inteligente de Dados:** Leitura e tratamento de arquivos `.xlsx` (padrão Google Forms) utilizando a biblioteca Pandas.
* **Interface Gráfica (GUI):** Interface moderna e intuitiva (com suporte a Dark Mode), facilitando o uso por usuários não-técnicos.
* **Gestão de Conflitos:** Algoritmo que previne que a mesma pessoa seja escalada para funções conflitantes no mesmo horário.
* **Multi-Exportação:** Gera a escala final em diversos formatos automaticamente:
    * 📄 **PDF:** Formatado e pronto para impressão ou mural.
    * 📅 **ICS:** Arquivo de calendário para integração direta com Google Calendar e Outlook.
    * 💬 **WhatsApp:** Texto pré-formatado para envio rápido em grupos.
    * 📊 **Excel:** Planilha organizada para controle administrativo.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Interface Gráfica:** [Coloque aqui a lib: Ex: CustomTkinter / PyQt5 / Tkinter]
* **Manipulação de Dados:** Pandas
* **Geração de Relatórios:** [Ex: ReportLab para PDF]
* **Compilação:** [Ex: PyInstaller] (para geração do executável .exe)
## 💾 Download
[![Download Windows](https://img.shields.io/badge/Download_Windows-.exe-2ea44f?style=for-the-badge&logo=windows)](https://github.com/Gbmarqss/PibShift/releases/download/v2.0/PibShift.exe)

> **Nota:** O Windows pode exibir um alerta de segurança por ser um .exe de desenvolvedor independente. Clique em "Mais informações" -> "Executar mesmo assim".

## 🚀 Como Executar

### Pré-requisitos
Certifique-se de ter o Python instalado em sua máquina.

### Instalação
1. Clone o repositório:
   ```bash
   git clone [https://github.com/Gbmarqss/PibShift.git](https://github.com/Gbmarqss/PibShift.git)
