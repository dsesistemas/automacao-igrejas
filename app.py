from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os
import json
import secrets
import asyncio
import logging
import threading
import base64 # Importar base64 para lidar com a imagem
import requests # <<<< ADICIONADO: Para chamadas HTTP à API de relés
from werkzeug.security import generate_password_hash, check_password_hash

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tentar importar simpleobsws e instalar se necessário
try:
    import simpleobsws
except ImportError:
    logger.info("Instalando módulo simpleobsws...")
    os.system('pip install simpleobsws')
    import simpleobsws

# Configuração inicial do Flask
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configurações do OBS WebSocket (usando a estrutura do código fornecido)
OBS_HOST = 'localhost'
OBS_PORT = 4444
OBS_PASSWORD = '123456789'  # IMPORTANTE: Use a senha correta do seu OBS WebSocket

# --- ADICIONADO: Configuração da API de Relés (Raspberry Pi) ---
# IMPORTANTE: Substitua pelo IP correto do seu Raspberry Pi
RELAY_API_BASE_URL = "http://10.149.0.136:5001" 
RELAY_TIMEOUT = 3 # Timeout em segundos para chamadas à API de relés

# Mapeamento de grupos para disjuntores
RELAY_GROUPS = {
    "frente": [1, 2],
    "meio": [3, 4],
    "fundo": [5, 6]
}
# --- FIM ADICIONADO ---

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classe de usuário para autenticação
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Banco de dados de usuários (simplificado)
users_db = {
    1: User(1, 'admin', generate_password_hash('admin123'))
}

@login_manager.user_loader
def load_user(user_id):
    return users_db.get(int(user_id))

# Função para conectar ao banco de dados SQLite
def get_db_connection():
    # Ajustar caminho para o diretório do projeto
    db_path = os.path.join(os.path.dirname(__file__), 'songs.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar banco de dados de músicas
def init_songs_db():
    db_path = os.path.join(os.path.dirname(__file__), 'songs.db')
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                categories TEXT
            )
        ''')
        sample_songs = [
            ('TUDO O QUE JESUS CONQUISTOU NA CRUZ', 'É DIREITO NOSSO E NOSSA HERANÇAnTODAS AS BENÇÃOS DE DEUS PRA NÓSnTOMAMOS POSSE É NOSSA HERANÇAn TODA VIDA TODO PODERnTUDO O QUE DEUS TEM PARA DARnABRIMOS NOSSAS VIDAS PRA RECEBERnNADA MAIS NOS RESISTIRÁn MAIOR É O QUE ESTÁ EM NÓSnDO QUE O QUE ESTÁ NO MUNDO', 'SEXTA, SEXTA-FEIRA'),
            ('O REI E O LADRÃO', 'MEUS OLHOS TÃO CANSADOSnE MARCADOS PELA DORnNÃO ME IMPORTAVA MAIS A VIDAnSEM QUALQUER VALORnHUMILHADO EM UMA CRUZnVENDO ÓDIO EM CADA OLHAR', 'CONHECIDAS, DOMINGO, DOMINGO, QUARTA, QUARTA-FEIRA, SEXTA, SEXTA-FEIRA')
        ]
        cursor.executemany('INSERT INTO songs (title, content, categories) VALUES (?, ?, ?)', sample_songs)
        conn.commit()
        conn.close()
        logger.info("Banco de dados de músicas inicializado com exemplos")

# Função genérica para requisições ao OBS (do código fornecido)
async def obs_request(request_type, request_data=None):
    parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False)
    ws = simpleobsws.WebSocketClient(
        url=f'ws://{OBS_HOST}:{OBS_PORT}',
        password=OBS_PASSWORD,
        identification_parameters=parameters
    )
    await ws.connect()
    await ws.wait_until_identified()
    response = await ws.call(simpleobsws.Request(request_type, request_data or {}))
    await ws.disconnect()
    if response.ok():
        return response.responseData
    else:
        status = response.requestStatus
        error_message = status.comment if hasattr(status, 'comment') and status.comment else f'Código de erro: {status.code}'
        raise Exception(f'Falha na requisição OBS ({request_type}): {error_message}')

# Rotas para autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        for user_id, user in users_db.items():
            if user.username == username and user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))
        flash('Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rotas principais do aplicativo
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/hinario')
@login_required
def hinario():
    return render_template('hinario.html')

# API para busca de músicas
@app.route('/api/search_songs', methods=['POST'])
@login_required
def search_songs():
    search_term = request.form.get('search_term', '')
    if not search_term:
        return jsonify([])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(""" 
        SELECT * FROM songs 
        WHERE title LIKE ? OR content LIKE ? OR categories LIKE ?
        LIMIT 10
    """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    songs = cursor.fetchall()
    conn.close()
    result = []
    for song in songs:
        content_processed = song['content'].replace('n', '; ')
        result.append({
            'id': song['id'],
            'title': song['title'],
            'content': content_processed,
            'categories': song['categories']
        })
    return jsonify(result)

# API para controle do OBS Studio
@app.route('/api/obs/switch_scene', methods=['POST'])
@login_required
def switch_obs_scene():
    scene_name = request.form.get('scene_name')
    if not scene_name:
        return jsonify({'success': False, 'message': 'Nome da cena não fornecido'}), 400
    def run_async_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(obs_request('SetCurrentProgramScene', {'sceneName': scene_name}))
            logger.info(f"Comando para alterar cena para '{scene_name}' enviado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao tentar alterar cena para '{scene_name}': {str(e)}")
        finally:
            loop.close()
    thread = threading.Thread(target=run_async_task)
    thread.daemon = True
    thread.start()
    return jsonify({'success': True, 'message': f'Comando enviado para alterar para a cena {scene_name}'})

@app.route('/api/obs/scenes', methods=['GET'])
@login_required
def get_obs_scenes():
    try:
        scenes_data = asyncio.run(obs_request('GetSceneList'))
        scenes = [scene['sceneName'] for scene in scenes_data.get('scenes', [])]
        return jsonify({'success': True, 'scenes': scenes})
    except Exception as e:
        logger.error(f"Erro ao buscar lista de cenas do OBS: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao buscar cenas: {str(e)}'}), 500

@app.route('/api/obs/preview', methods=['GET'])
@login_required
def get_obs_preview():
    try:
        current_program_scene_data = asyncio.run(obs_request('GetCurrentProgramScene'))
        current_scene_name = current_program_scene_data.get('currentProgramSceneName')
        if not current_scene_name:
            raise Exception("Não foi possível obter a cena atual do programa.")
        screenshot_data = asyncio.run(obs_request('GetSourceScreenshot', {
            'sourceName': current_scene_name,
            'imageFormat': 'jpeg',
            'imageWidth': 640,
            'imageCompressionQuality': 70
        }))
        image_data_uri = screenshot_data.get('imageData')
        if not image_data_uri:
             raise Exception("Não foi possível obter os dados da imagem do screenshot.")
        return jsonify({'success': True, 'imageData': image_data_uri})
    except Exception as e:
        logger.error(f"Erro ao obter preview do OBS: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao obter preview: {str(e)}'}), 500

@app.route('/api/obs/status', methods=['GET'])
@login_required
def check_obs_status():
    try:
        asyncio.run(obs_request('GetVersion'))
        return jsonify({'status': 'connected', 'message': 'Conectado ao OBS Studio'}) 
    except Exception as e:
        logger.error(f"Falha ao verificar status do OBS: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Não foi possível conectar ao OBS: {str(e)}'})

# --- ADICIONADO: API PARA CONTROLE DOS RELÉS ---
@app.route('/api/relay/control', methods=['POST'])
@login_required
def control_relay_via_api():
    relay_id = request.form.get('relay_id') # Pode ser número (1-6) ou grupo ('frente', 'meio', 'fundo')
    state = request.form.get('state') # 'on' ou 'off'

    if not relay_id or state not in ['on', 'off']:
        logger.warning(f"Requisição inválida para controle de relé: ID={relay_id}, Estado={state}")
        return jsonify({'success': False, 'message': 'Parâmetros inválidos (relay_id e state são obrigatórios)'}), 400

    relays_to_control = []
    is_group = False

    # Verifica se é um controle de grupo
    if relay_id in RELAY_GROUPS:
        is_group = True
        relays_to_control = RELAY_GROUPS[relay_id]
        control_target_log = f"grupo '{relay_id}' (Relés: {relays_to_control})"
    else:
        # Tenta converter para número (controle individual)
        try:
            relay_num = int(relay_id)
            if 1 <= relay_num <= 6:
                relays_to_control.append(relay_num)
                control_target_log = f"relé {relay_num}"
            else:
                raise ValueError("Número do relé fora do intervalo 1-6")
        except ValueError:
            logger.warning(f"ID de relé inválido recebido: {relay_id}")
            return jsonify({'success': False, 'message': f'ID de relé inválido: {relay_id}'}), 400

    logger.info(f"Recebido comando para alterar {control_target_log} para {state.upper()}")

    all_success = True
    error_messages = []

    # Envia comando para cada relé individualmente
    for r_num in relays_to_control:
        api_url = f"{RELAY_API_BASE_URL}/relay/{r_num}/{state}"
        try:
            response = requests.post(api_url, timeout=RELAY_TIMEOUT)
            response.raise_for_status() # Levanta erro para status 4xx/5xx
            response_data = response.json()
            if not response_data.get('success'):
                all_success = False
                error_msg = response_data.get('message', f'Erro na API do relé {r_num}')
                error_messages.append(error_msg)
                logger.error(f"Falha ao controlar relé {r_num} via API: {error_msg}")
            else:
                logger.info(f"Relé {r_num} controlado com sucesso via API para {state.upper()}")

        except requests.exceptions.Timeout:
            all_success = False
            error_msg = f"Timeout ao conectar com API do relé {r_num}"
            error_messages.append(error_msg)
            logger.error(error_msg)
        except requests.exceptions.RequestException as e:
            all_success = False
            error_msg = f"Erro de conexão/requisição para API do relé {r_num}: {e}"
            error_messages.append(error_msg)
            logger.error(error_msg)
        except Exception as e:
            all_success = False
            error_msg = f"Erro inesperado ao controlar relé {r_num}: {e}"
            error_messages.append(error_msg)
            logger.error(error_msg)

    # Personalizar mensagem com base no tipo (grupo ou individual)
    if is_group:
        # Mapear nomes de grupos para termos de teto
        teto_names = {
            "frente": "FRENTE",
            "meio": "MEIO",
            "fundo": "FUNDO"
        }
        teto_name = teto_names.get(relay_id, relay_id.upper())
        success_message = f'Teto \'{teto_name}\' alterado(s) para {state.upper()} com sucesso'
        error_message = f'Falha ao alterar Teto \'{teto_name}\'. Erros: {"; ".join(error_messages)}'
    else:
        # Para controles individuais (relés)
        success_message = f'Fileira {relay_id} alterado(s) para {state.upper()} com sucesso'
        error_message = f'Falha ao alterar Fileira {relay_id}. Erros: {"; ".join(error_messages)}'
    
    if all_success:
        return jsonify({'success': True, 'message': success_message}) 
    else:
        return jsonify({'success': False, 'message': error_message}), 500


# Rota para obter o status inicial dos relés (opcional, mas bom para sincronizar a UI)
@app.route('/api/relay/initial_status', methods=['GET'])
@login_required
def get_initial_relay_status():
    api_url = f"{RELAY_API_BASE_URL}/relay/status"
    try:
        response = requests.get(api_url, timeout=RELAY_TIMEOUT)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get('success'):
            logger.info("Status inicial dos relés obtido com sucesso da API.")
            return jsonify({"success": True, "status": response_data.get('status', {})})
        else:
            raise Exception(response_data.get('message', "Erro na API de status dos relés"))
    except requests.exceptions.Timeout:
        error_msg = "Timeout ao obter status inicial dos relés da API."
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 503 # Service Unavailable
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro de conexão/requisição ao obter status inicial dos relés: {e}"
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 503
    except Exception as e:
        error_msg = f"Erro inesperado ao obter status inicial dos relés: {e}"
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
# --- FIM ADICIONADO ---

# REMOVIDO: Rota de simulação de luzes
# @app.route('/api/lights/toggle', methods=['POST'])
# @login_required
# def toggle_lights():
#     light_id = request.form.get('light_id')
#     state = request.form.get('state', 'toggle')
#     logger.info(f"[SIMULAÇÃO] Alterando luz {light_id} para {state}")
#     return jsonify({'success': True, 'message': f'Luz {light_id} alterada para {state}'})

if __name__ == '__main__':
    init_songs_db()
    # Adicionar requests à lista de dependências se não estiver
    try:
        import requests
    except ImportError:
        logger.info("Instalando módulo requests...")
        os.system('pip install requests')
    
    app.run(host='0.0.0.0', port=5000, debug=True)