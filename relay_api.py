# Automação DSE - Sistema de Automação para Igrejas

Este sistema integra o controle do OBS Studio para transmissões e um sistema de controle de disjuntores via Raspberry Pi para automação de iluminação, além de um hinário digital para exibição de letras de músicas.

## Índice

1. [Visão Geral](#visão-geral)
2. [Requisitos do Sistema](#requisitos-do-sistema)
3. [Instalação no PC](#instalação-no-pc)
4. [Instalação no Raspberry Pi](#instalação-no-raspberry-pi)
5. [Configuração do OBS Studio](#configuração-do-obs-studio)
6. [Conexão entre PC e Raspberry Pi](#conexão-entre-pc-e-raspberry-pi)
7. [Uso do Hinário (Banco de Dados songs.db)](#uso-do-hinário-banco-de-dados-songsdb)
8. [Inicialização Automática](#inicialização-automática)
9. [Solução de Problemas](#solução-de-problemas)

## Visão Geral

O sistema é composto por dois componentes principais:

1. **Aplicação Web (PC)**: Interface para controle do OBS Studio e dos disjuntores, além do hinário digital
2. **API de Relés (Raspberry Pi)**: Controla os relés físicos conectados aos disjuntores da igreja

```
[PC com OBS Studio] <-- WebSocket --> [Aplicação Web Flask]
                                            |
                                            v
                                      [API HTTP REST] --> [Raspberry Pi] --> [Relés] --> [Disjuntores]
```

## Requisitos do Sistema

### Para o PC:
- Windows 10/11 ou Linux
- Python 3.7 ou superior
- OBS Studio 28+ com plugin WebSocket
- Navegador web moderno (Chrome, Firefox, Edge)
- Conexão de rede com o Raspberry Pi

### Para o Raspberry Pi:
- Raspberry Pi 4 Model B (recomendado)
- Raspbian/Raspberry Pi OS
- Python 3.7 ou superior
- Módulo de 6 relés (5V)
- Conexões para as contatoras dos disjuntores

## Instalação no PC

### 1. Preparação do Ambiente

1. **Instale o Python**:
   - Baixe e instale o Python em [python.org](https://www.python.org/downloads/)
   - Durante a instalação, marque a opção "Add Python to PATH"

2. **Baixe os Arquivos do Projeto**:
   - Baixe e extraia o arquivo ZIP do projeto em uma pasta de sua escolha (ex: `C:\automacao-igrejas (PC)` ou `~/automacao-igrejas (Raspberry Pi)`)
   - Download: https://github.com/dsesistemas/automacao-igrejas

3. **Abra o Terminal/Prompt de Comando**:
   - Windows: Pressione Win+R, digite `cmd` e pressione Enter
   - Linux/Mac: Abra o Terminal

4. **Navegue até a Pasta do Projeto**:
   ```
   cd caminho/para/automacao-igrejas
   ```

### 2. Configuração do Ambiente Virtual

1. **Crie um Ambiente Virtual**:
   - Windows:
     ```
     python -m venv venv
     ```
   - Linux/Mac:
     ```
     python3 -m venv venv
     ```

2. **Ative o Ambiente Virtual**:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```
     source venv/bin/activate
     ```

3. **Instale as Dependências**:
   ```
   pip install -r requirements_windows.txt
   ```

   > **IMPORTANTE**: Use o arquivo `requirements_windows.txt` no PC, não o arquivo `requirements_raspberry.txt`. O pacote RPi.GPIO não é compatível com Windows.

### 3. Configuração da Aplicação

1. **Configure a Conexão com o OBS Studio**:
   - Abra o arquivo `app.py` em um editor de texto
   - Localize as seguintes linhas:
     ```python
     OBS_HOST = 'localhost'
     OBS_PORT = 4444
     OBS_PASSWORD = '123456789'  # IMPORTANTE: Use a senha correta do seu OBS WebSocket
     ```
   - Ajuste conforme necessário (veja a seção [Configuração do OBS Studio](#configuração-do-obs-studio))

2. **Configure a Conexão com o Raspberry Pi**:
   - No mesmo arquivo `app.py`, localize a linha:
     ```python
     RELAY_API_BASE_URL = "http://YOUR_RASPBERRY_PI_IP:5001"
     ```
   - Substitua `YOUR_RASPBERRY_PI_IP` pelo endereço IP real do seu Raspberry Pi
   - Exemplo: `RELAY_API_BASE_URL = "http://192.168.1.100:5001"`

### 4. Execução da Aplicação

1. **Inicie o OBS Studio** (veja a seção [Configuração do OBS Studio](#configuração-do-obs-studio))

2. **Execute a Aplicação Web**:
   ```
   python app.py
   ```

3. **Acesse a Interface Web**:
   - No mesmo PC: Abra o navegador e acesse `http://localhost:5000`
   - Em outros dispositivos na mesma rede: `http://IP_DO_PC:5000`

4. **Faça Login**:
   - Usuário padrão: `admin`
   - Senha padrão: `admin123`

## Instalação no Raspberry Pi

### 1. Preparação do Ambiente

1. **Atualize o Sistema**:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. **Instale as Dependências do Sistema**:
   ```bash
   sudo apt install -y python3-pip python3-venv git
   ```

3. **Crie uma Pasta para o Projeto**:
   ```bash
   mkdir -p ~/automacao-igrejas
   cd ~/automacao-igrejas
   ```

### 2. Configuração do Script de Controle de Relés

1. **Baixe o Arquivo `relay_api.py`**:
   ```bash
   wget https://raw.github.com/dsesistemas/automacao-igrejas/main/relay_api.py
   ```

2. **Crie um Ambiente Virtual**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Baixe o arquivo "requirements_raspberry.txt" e Instale as Dependências**:
   ```bash
   wget https://raw.github.com/dsesistemas/automacao-igrejas/main/requirements_raspberry.txt
   pip install -r requirements_raspberry.txt
   ```
   
   > **IMPORTANTE**: Use o arquivo `requirements_raspberry.txt` no Raspberry Pi, que contém as dependências necessárias para controle dos GPIOs.

### 3. Configuração dos Pinos GPIO

Por padrão, o script `relay_api.py` está configurado para usar os seguintes pinos GPIO:

| Relé/Disjuntor | Pino GPIO | Pino Físico |
|----------------|-----------|-------------|
| 1              | 2         | 3           |
| 2              | 18        | 12          |
| 3              | 27        | 13          |
| 4              | 22        | 15          |
| 5              | 23        | 16          |
| 6              | 24        | 18          |

Se precisar alterar esta configuração:

1. **Abra o Arquivo `relay_api.py`**:
   ```bash
   nano relay_api.py
   ```

2. **Localize e Edite o Dicionário `RELAY_PINS`**:
   ```python
   RELAY_PINS = {
       1: 2,   # Disjuntor 1 (GPIO 2, Pino Físico 3)
       2: 18,  # Disjuntor 2 (GPIO 18, Pino Físico 12)
       3: 27,  # Disjuntor 3 (GPIO 27, Pino Físico 13)
       4: 22,  # Disjuntor 4 (GPIO 22, Pino Físico 15)
       5: 23,  # Disjuntor 5 (GPIO 23, Pino Físico 16)
       6: 24,  # Disjuntor 6 (GPIO 24, Pino Físico 18)
   }
   ```

3. **Salve o Arquivo**: Pressione Ctrl+X, depois Y e Enter

### 4. Conexões Físicas

1. **Conecte o Módulo de Relés ao Raspberry Pi**:
   - VCC do módulo de relés → 5V do Raspberry Pi
   - GND do módulo de relés → GND do Raspberry Pi
   - IN1-IN6 do módulo de relés → GPIOs configurados no `relay_api.py`

2. **Conecte as Contatoras aos Relés**:
   - Cada relé deve ser conectado à bobina da contatora correspondente
   - Siga as especificações elétricas das contatoras para conexão correta

### 5. Execução da API de Relés

1. **Anote o Endereço IP do Raspberry Pi**:
   ```bash
   hostname -I
   ```
   - Use este IP para configurar o `app.py` no PC
   

2. **Execute o Script**:
   ```bash
   python3 relay_api.py
   ```
   
3. **Verifique o Funcionamento**:
   - O servidor será iniciado na porta 5001
   - Todos os relés serão inicializados como ligados (ON)

## Configuração do OBS Studio

### 1. Instalação do OBS Studio

1. **Baixe e Instale o OBS Studio**:
   - Acesse [obsproject.com](https://obsproject.com/) e baixe a versão para seu sistema operacional
   - Siga as instruções de instalação

2. **Verifique o Plugin WebSocket**:
   - O OBS Studio 28+ já inclui o plugin WebSocket v5
   - Não é necessário instalar plugins adicionais

### 2. Configuração do WebSocket

1. **Abra o OBS Studio**

2. **Acesse as Configurações do WebSocket**:
   - Vá para o menu: `Ferramentas` > `Configurações do WebSocket`

3. **Habilite o Servidor WebSocket**:
   - Marque a caixa `Habilitar servidor WebSocket`

4. **Configure a Porta do Servidor**:
   - O campo `Porta do Servidor` deve estar configurado com o valor `4444` (padrão)
   - Se precisar usar outra porta, anote-a para atualizar no `app.py`

5. **Configure a Autenticação (Senha)**:
   - Marque a caixa `Habilitar Autenticação`
   - Defina uma senha segura
   - **IMPORTANTE**: Anote esta senha para configurar no `app.py`

6. **Aplique as Configurações**:
   - Clique no botão `Aplicar` e depois em `OK`

### 3. Configuração das Cenas

1. **Crie as Cenas Necessárias**:
   - Crie as cenas que você precisará para o culto
   - O webapp carregará automaticamente todas as cenas disponíveis

## Conexão entre PC e Raspberry Pi

### 1. Verificação da Rede

1. **Certifique-se que Ambos os Dispositivos Estão na Mesma Rede**:
   - O PC e o Raspberry Pi devem estar conectados à mesma rede local
   - Preferencialmente, use conexões cabeadas para maior estabilidade

2. **Teste a Comunicação**:
   - No PC, abra o terminal/prompt de comando e execute:
     ```
     ping IP_DO_RASPBERRY_PI
     ```
   - Você deve receber respostas sem perda de pacotes

### 2. Configuração do Firewall

1. **No Raspberry Pi**:
   - Caso esteja utilizando firewall, certifique-se que a porta 5001 está liberada:
     ```bash
     sudo ufw allow 5001/tcp
     ```

2. **No PC**:
   - Certifique-se que a porta 5000 está liberada no firewall do Windows/Linux

### 3. Teste da API de Relés

1. **Verifique se a API está Funcionando**:
   - No navegador do PC, acesse:
     ```
     http://IP_DO_RASPBERRY_PI:5001/relay/status
     ```
   - Deve retornar um JSON com o status de todos os relés
   - Exemplo: `{"status":{"1":"on","2":"on","3":"on","4":"on","5":"on","6":"on"},"success":true}`

## Uso do Hinário (Banco de Dados songs.db)

O sistema inclui um banco de dados SQLite (`songs.db`) com músicas para o hinário digital.

### 1. Estrutura do Banco de Dados

O banco de dados contém uma tabela principal `songs` com os seguintes campos:
- `id`: Identificador único da música
- `title`: Título da música
- `content`: Letra da música (com quebras de linha)
- `categories`: Categorias separadas por vírgula (ex: "Adoração, Louvor")

### 2. Pesquisa de Músicas

Na interface web, acesse a página do Hinário para:
- Pesquisar músicas por título
- Pesquisar músicas por conteúdo (letra)
- Filtrar por categoria

### 3. Adição de Novas Músicas

#### Método 1: Usando o DB Browser for SQLite

1. **Baixe e Instale o DB Browser for SQLite**:
   - Acesse [sqlitebrowser.org](https://sqlitebrowser.org/dl/)
   - Baixe e instale a versão para seu sistema operacional

2. **Abra o Banco de Dados**:
   - Inicie o DB Browser for SQLite
   - Clique em "Abrir Banco de Dados"
   - Navegue até a pasta do projeto e selecione `songs.db`

3. **Adicione Novas Músicas**:
   - Clique na aba "Executar SQL"
   - Execute comandos como:
     ```sql
     INSERT INTO songs (title, content, categories) 
     VALUES ('TÍTULO DA MÚSICA', 'LETRA DA MÚSICA
     COM QUEBRAS DE LINHA
     ONDE NECESSÁRIO', 'CATEGORIA1, CATEGORIA2');
     ```
   - Clique em "Escrever Alterações" para salvar

#### Método 2: Importação em Massa

Para importar muitas músicas de uma vez:

1. **Crie um Arquivo CSV**:
   - Crie um arquivo `musicas.csv` com o formato:
     ```
     "TÍTULO","LETRA","CATEGORIAS"
     ```

2. **Crie um Script de Importação**:
   - Crie um arquivo `importar_musicas.py`:
     ```python
     import sqlite3
     import csv

     # Conectar ao banco de dados
     conn = sqlite3.connect('songs.db')
     cursor = conn.cursor()

     # Ler o arquivo CSV
     with open('musicas.csv', 'r', encoding='utf-8') as file:
         reader = csv.reader(file)
         next(reader)  # Pular cabeçalho
         for row in reader:
             title, content, categories = row
             cursor.execute(
                 'INSERT INTO songs (title, content, categories) VALUES (?, ?, ?)',
                 (title, content, categories)
             )

     # Salvar alterações
     conn.commit()
     conn.close()
     print("Importação concluída!")
     ```

3. **Execute o Script**:
   ```
   python importar_musicas.py
   ```

## Inicialização Automática

### No PC Windows

#### Método 1: Usando o Task Scheduler (Agendador de Tarefas)

1. **Crie um Script Batch (.bat)**:
   - Abra o Bloco de Notas
   - Cole o seguinte código (ajuste os caminhos conforme necessário):
     ```batch
     @echo off
     cd /d C:\caminho\para\automacao-igrejas
     call venv\Scripts\activate
     python app.py
     pause
     ```
   - Salve como `iniciar_automacao.bat` na pasta do projeto

2. **Configure o Task Scheduler**:
   - Pressione Win+R, digite `taskschd.msc` e pressione Enter
   - Clique em "Criar Tarefa Básica" no painel direito
   - Dê um nome como "Automacao DSE"
   - Selecione "Quando o computador é iniciado"
   - Escolha "Iniciar um programa"
   - Navegue até o arquivo .bat que você criou
   - Conclua o assistente

### No Raspberry Pi

#### Usando systemd

1. **Crie um Arquivo de Serviço**:
   ```bash
   sudo nano /etc/systemd/system/relay-api.service
   ```

2. **Adicione o Seguinte Conteúdo**:
   ```ini
   [Unit]
   Description=Relay API Service for Church Automation
   After=network.target

   [Service]
   User=dse
   WorkingDirectory=/home/dse/automacao-dse
   ExecStart=/home/dse/automacao-dse/venv/bin/python /home/dse/automacao-dse/relay_api.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Salve o Arquivo**: Pressione Ctrl+X, depois Y e Enter

4. **Habilite e Inicie o Serviço**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable relay-api.service
   sudo systemctl start relay-api.service
   ```

5. **Verifique o Status**:
   ```bash
   sudo systemctl status relay-api.service
   ```

## Solução de Problemas

### Problemas com o OBS Studio

1. **Erro ao conectar ao OBS**:
   - Verifique se o OBS Studio está aberto
   - Confirme se o servidor WebSocket está habilitado no OBS
   - Verifique se o `OBS_HOST`, `OBS_PORT` e `OBS_PASSWORD` no arquivo `app.py` estão corretos
   - Verifique se não há um firewall bloqueando a conexão

2. **Preview não aparece**:
   - Verifique se há pelo menos uma cena configurada no OBS
   - Verifique os logs no terminal para mensagens de erro específicas
   - Tente reiniciar o OBS Studio

### Problemas com o Controle de Disjuntores

1. **Erro ao controlar disjuntores**:
   - Verifique se o Raspberry Pi está ligado e na mesma rede
   - Confirme se o IP do Raspberry Pi está correto no `app.py`
   - Verifique se a API de relés está em execução no Raspberry Pi
   - Teste a API diretamente: `http://IP_DO_RASPBERRY:5001/relay/status`

2. **Relés não acionam**:
   - Verifique as conexões físicas entre o Raspberry Pi e a placa de relés
   - Confirme se os números dos GPIOs no `relay_api.py` correspondem às conexões físicas
   - Teste os relés manualmente usando um script simples de GPIO

### Problemas de Instalação

1. **Erro ao instalar RPi.GPIO no Windows**:
   - Este é um erro esperado, pois RPi.GPIO é específico para Raspberry Pi
   - Use o arquivo `requirements_windows.txt` em vez de `requirements.txt` no PC Windows
   - Use o arquivo `requirements_raspberry.txt` no Raspberry Pi

2. **Erro de Módulo não Encontrado (`ImportError`)**:
   - Certifique-se de que o ambiente virtual está ativo
   - No Windows: `pip install -r requirements_windows.txt`
   - No Raspberry Pi: `pip install -r requirements_raspberry.txt`

### Problemas de Rede

1. **Não consegue acessar a API do Raspberry Pi**:
   - Verifique se o Raspberry Pi e o PC estão na mesma rede
   - Teste a conexão com `ping IP_DO_RASPBERRY_PI`
   - Verifique se o firewall está permitindo a conexão na porta 5001
   - Confirme se o script `relay_api.py` está em execução no Raspberry Pi

2. **Não consegue acessar o webapp**:
   - Verifique se o script `app.py` está em execução no PC
   - Teste acessando `http://localhost:5000` no próprio PC
   - Verifique se o firewall está permitindo a conexão na porta 5000

### Logs para Diagnóstico

1. **No Raspberry Pi**:
   - Observe a saída do terminal ao executar `python3 relay_api.py`
   - Se estiver rodando como serviço: `sudo journalctl -u relay-api.service -f`

2. **No PC**:
   - Observe a saída do terminal ao executar `python app.py`
   - Verifique mensagens de erro no console do navegador (F12 > Console)

Para problemas não listados aqui, entre em contato com o suporte técnico ou consulte a documentação adicional.
