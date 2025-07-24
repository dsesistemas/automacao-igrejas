#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, abort
import RPi.GPIO as GPIO
import atexit
import logging

# --- Configuração ---
RELAY_PINS = {
    1: 2,  # Disjuntor 1
    2: 17,  # Disjuntor 2
    3: 27,  # Disjuntor 3
    4: 22,  # Disjuntor 4
    5: 23,  # Disjuntor 5
    6: 24,  # Disjuntor 6
}

# Lógica do Relé: HIGH = Desligado (OFF), LOW = Ligado (ON)
# (Ajuste se sua placa de relé for Active HIGH)
RELAY_ON_STATE = GPIO.LOW
RELAY_OFF_STATE = GPIO.HIGH

# Estado inicial desejado ao iniciar o script
INITIAL_STATE = RELAY_ON_STATE # Todos ligados

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Inicialização do Flask ---
app = Flask(__name__)

# --- Inicialização do GPIO ---
def setup_gpio():
    logger.info("Configurando GPIO...")
    GPIO.setmode(GPIO.BCM)  # Usar numeração BCM
    GPIO.setwarnings(False) # Desabilitar avisos
    for relay_num, pin in RELAY_PINS.items():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, INITIAL_STATE) # Define o estado inicial
        logger.info(f"Relé {relay_num} (GPIO {pin}) configurado para estado inicial: {"ON" if INITIAL_STATE == GPIO.LOW else "OFF"}")
    logger.info("GPIO configurado com sucesso.")

def cleanup_gpio():
    logger.info("Limpando configurações do GPIO...")
    GPIO.cleanup()
    logger.info("GPIO limpo.")

# Registra a função de limpeza para ser chamada ao sair
atexit.register(cleanup_gpio)

# --- Funções Auxiliares ---
def set_relay_state(relay_num, state):
    if relay_num not in RELAY_PINS:
        logger.warning(f"Tentativa de controlar relé inválido: {relay_num}")
        return False, "Número do relé inválido"
        
    pin = RELAY_PINS[relay_num]
    gpio_state = RELAY_OFF_STATE if state == "off" else RELAY_ON_STATE
    
    try:
        GPIO.output(pin, gpio_state)
        logger.info(f"Relé {relay_num} (GPIO {pin}) alterado para {state.upper()}")
        return True, f"Relé {relay_num} alterado para {state.upper()}"
    except Exception as e:
        logger.error(f"Erro ao alterar estado do Relé {relay_num} (GPIO {pin}): {e}")
        return False, f"Erro ao alterar estado do Relé {relay_num}"

def get_relay_state(relay_num):
    if relay_num not in RELAY_PINS:
        return None
    pin = RELAY_PINS[relay_num]
    current_gpio_state = GPIO.input(pin)
    return "on" if current_gpio_state == RELAY_ON_STATE else "off"

# --- Rotas da API ---
@app.route("/relay/<int:relay_num>/<string:state>", methods=["POST"])
def control_relay(relay_num, state):
    state = state.lower()
    if state not in ["on", "off"]:
        logger.warning(f"Estado inválido solicitado para relé {relay_num}: {state}")
        abort(400, description="Estado inválido. Use 'on' ou 'off'.")
        
    success, message = set_relay_state(relay_num, state)
    
    if success:
        return jsonify({"success": True, "relay": relay_num, "state": state, "message": message})
    else:
        # Se o relé for inválido, retorna 404, senão 500
        status_code = 404 if "inválido" in message else 500
        return jsonify({"success": False, "relay": relay_num, "state": state, "message": message}), status_code

@app.route("/relay/status", methods=["GET"])
def get_all_relays_status():
    status = {}
    try:
        for relay_num in RELAY_PINS:
            status[relay_num] = get_relay_state(relay_num)
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logger.error(f"Erro ao obter status dos relés: {e}")
        return jsonify({"success": False, "message": "Erro ao obter status dos relés"}), 500

@app.route("/relay/<int:relay_num>/status", methods=["GET"])
def get_single_relay_status(relay_num):
    state = get_relay_state(relay_num)
    if state is None:
        logger.warning(f"Tentativa de obter status de relé inválido: {relay_num}")
        abort(404, description="Número do relé inválido")
    return jsonify({"success": True, "relay": relay_num, "state": state})

# --- Execução ---
if __name__ == "__main__":
    try:
        setup_gpio()
        logger.info("Iniciando servidor Flask para API de Relés...")
        # Executa na porta 5001 para não conflitar com o app principal se rodar no mesmo lugar
        app.run(host="0.0.0.0", port=5001, debug=False) 
    except Exception as e:
        logger.critical(f"Falha crítica ao iniciar a API de Relés: {e}")
    finally:
        cleanup_gpio() # Garante a limpeza mesmo se o app falhar ao iniciar

