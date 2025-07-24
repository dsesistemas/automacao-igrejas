
// JavaScript para a página principal (automação)
let obsPreviewInterval = null; // Variável para controlar o intervalo de atualização
const PREVIEW_UPDATE_INTERVAL = 2000; // Intervalo em milissegundos (2 segundos)

document.addEventListener("DOMContentLoaded", function () {
    // Verificar status do OBS e carregar botões de cena
    checkOBSStatus();
    loadSceneButtons();

    // --- ADICIONADO: Inicializar controles de disjuntores ---
    initializeRelayControls();
    // --- FIM ADICIONADO ---

    // --- INICIAR ATUALIZAÇÃO DO PREVIEW --- 
    startObsPreviewUpdate();
    // --- FIM --- 

    // Verificar status a cada 30 segundos
    setInterval(checkOBSStatus, 30000);
});

// Função para verificar status do OBS
function checkOBSStatus() {
    fetch("/api/obs/status")
        .then(response => response.json())
        .then(data => {
            // REMOVIDO: Código que referenciava status-alert/message que não existe mais
            // const statusAlert = document.getElementById("obs-status-alert");
            // const statusMessage = document.getElementById("obs-status-message");
            // if (!statusAlert || !statusMessage) return;

            if (data.status === "connected") {
                // statusAlert.className = "alert alert-success";
                // statusMessage.textContent = "Conectado ao OBS Studio";
                console.log("OBS Status: Conectado");
                // Se estava desconectado e conectou, iniciar preview
                if (!obsPreviewInterval) {
                    startObsPreviewUpdate();
                }
            } else {
                // statusAlert.className = "alert alert-danger";
                // statusMessage.textContent = data.message || "Erro desconhecido ao conectar ao OBS";
                console.error("OBS Status: Desconectado ou Erro -", data.message);
                // Se desconectou, parar preview
                stopObsPreviewUpdate();
                showPreviewError("OBS desconectado");
            }
        })
        .catch(error => {
            console.error("Erro ao verificar status:", error);
            // const statusAlert = document.getElementById("obs-status-alert");
            // const statusMessage = document.getElementById("obs-status-message");
            // if (statusAlert && statusMessage) {
            //     statusAlert.className = "alert alert-danger";
            //     statusMessage.textContent = "Erro de rede ao verificar status do OBS.";
            // }
            stopObsPreviewUpdate();
            showPreviewError("Erro de rede");
        });
}

// Função para carregar botões de cena dinamicamente
function loadSceneButtons() {
    const container = document.getElementById("scene-buttons-container");
    if (!container) return;

    container.innerHTML =
        `<div class="col-12 text-center">
            <div class="spinner-border text-light" role="status"> <!-- Mantido text-light -->
                <span class="visually-hidden">Carregando cenas...</span>
            </div>
        </div>`;

    fetch("/api/obs/scenes")
        .then(response => response.json())
        .then(data => {
            container.innerHTML = "";

            if (data.success && data.scenes && data.scenes.length > 0) {
                data.scenes.forEach(sceneName => {
                    const col = document.createElement("div");
                    col.className = "col-6 col-md-4 col-lg-3 mb-2";
                    const button = document.createElement("button");
                    // Usando btn-secondary para manter o padrão visual anterior
                    button.className = "btn btn-secondary w-100 scene-btn";
                    button.setAttribute("data-scene", sceneName);
                    button.textContent = sceneName;
                    button.addEventListener("click", function () {
                        switchScene(sceneName);
                    });
                    col.appendChild(button);
                    container.appendChild(col);
                });
            } else if (data.success && data.scenes.length === 0) {
                container.innerHTML =
                    `<div class="col-12 text-center text-muted">Nenhuma cena encontrada no OBS.</div>`;
            } else {
                container.innerHTML =
                    `<div class="col-12 text-center text-danger">Erro ao carregar cenas: 
                    ${(data.message || "Erro desconhecido")}
                    </div>`;
            }
        })
        .catch(error => {
            console.error("Erro ao buscar cenas:", error);
            container.innerHTML =
                `<div class="col-12 text-center text-danger">Erro de rede ao carregar cenas. Verifique a conexão com o servidor.</div>`;
        });
}

// Função para alternar cenas do OBS
function switchScene(sceneName) {
    const button = document.querySelector(`.scene-btn[data-scene="${sceneName}"]`);
    if (button) {
        const originalText = button.textContent;
        button.textContent = "Enviando...";
        button.disabled = true;
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 1000);
    }

    fetch("/api/obs/switch_scene", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `scene_name=${encodeURIComponent(sceneName)}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`Comando enviado para: ${sceneName}`);
                showNotification(`Comando enviado para: ${sceneName}`);
            } else {
                console.error("Erro ao alterar cena:", data.message);
                showNotification(`Erro: ${data.message || "Erro desconhecido"}`, "error");
            }
        })
        .catch(error => {
            console.error("Erro na requisição:", error);
            showNotification("Erro de conexão ao tentar alterar cena", "error");
        });
}

// --- ADICIONADO: Funções para controle de disjuntores/relés ---
function initializeRelayControls() {
    const individualSwitches = document.querySelectorAll(".individual-switch");
    const groupSwitches = document.querySelectorAll(".group-switch");

    individualSwitches.forEach(switchElement => {
        switchElement.addEventListener("change", function () {
            const relayId = this.getAttribute("data-disjuntor");
            const state = this.checked ? "on" : "off";
            controlRelay(relayId, state);
            // Atualizar estado do botão de grupo correspondente
            updateGroupSwitchesState();
        });
    });

    groupSwitches.forEach(switchElement => {
        switchElement.addEventListener("change", function () {
            const groupId = this.getAttribute("data-grupo");
            const state = this.checked ? "on" : "off";
            controlRelay(groupId, state);
            // Atualizar switches individuais do grupo (feedback visual)
            updateIndividualSwitchesForGroup(groupId, this.checked);
        });
    });

    // Buscar estado inicial dos relés para sincronizar a UI
    fetchInitialRelayStatus();
}

function controlRelay(relayId, state) {
    // Desabilitar temporariamente o switch para evitar cliques múltiplos
    const switchElement = document.getElementById(`disjuntor-switch-${relayId}`) || document.getElementById(`grupo-switch-${relayId}`);
    if (switchElement) switchElement.disabled = true;

    fetch("/api/relay/control", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `relay_id=${encodeURIComponent(relayId)}&state=${state}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Personalizar mensagem de log com base no tipo
                if (["frente", "meio", "fundo"].includes(relayId)) {
                    console.log(`Comando enviado para Teto ${relayId.toUpperCase()}: ${state}`);
                } else {
                    console.log(`Comando enviado para Fileira ${relayId}: ${state}`);
                }

                showNotification(data.message);
                // Se for grupo, atualiza estado dos individuais após sucesso
                if (["frente", "meio", "fundo"].includes(relayId)) {
                    updateIndividualSwitchesForGroup(relayId, state === "on");
                }
                // Atualiza estado dos grupos após qualquer mudança individual ou de grupo
                updateGroupSwitchesState();
            } else {

                console.error("Erro ao controlar relé:", data.message);
                showNotification(`Erro: ${data.message || "Falha no controle do relé"}`, "error");
                // Reverter o estado visual do switch em caso de erro
                if (switchElement) switchElement.checked = !switchElement.checked;
                // Re-sincronizar estado dos grupos se um controle falhar
                updateGroupSwitchesState();
            }
        })
        .catch(error => {
            console.error("Erro na requisição de controle do relé:", error);
            showNotification("Erro de conexão ao controlar relé", "error");
            // Reverter o estado visual do switch em caso de erro
            if (switchElement) switchElement.checked = !switchElement.checked;
            // Re-sincronizar estado dos grupos se um controle falhar
            updateGroupSwitchesState();
        })
        .finally(() => {
            // Reabilitar o switch após a resposta
            if (switchElement) {
                setTimeout(() => { switchElement.disabled = false; }, 500); // Pequeno delay
            }
        });
}

function fetchInitialRelayStatus() {
    fetch("/api/relay/initial_status")
        .then(response => response.json())
        .then(data => {
            if (data.success && data.status) {
                console.log("Status inicial dos relés:", data.status);
                for (const relayNum in data.status) {
                    const switchElement = document.getElementById(`disjuntor-switch-${relayNum}`);
                    if (switchElement) {
                        switchElement.checked = (data.status[relayNum] === "on");
                    }
                }
                // Atualizar estado dos botões de grupo com base nos individuais
                updateGroupSwitchesState();
                showNotification("Status dos disjuntores sincronizado.");
            } else {
                console.error("Erro ao buscar status inicial dos relés:", data.message);
                showNotification("Falha ao sincronizar status dos disjuntores", "error");
            }
        })
        .catch(error => {
            console.error("Erro de rede ao buscar status inicial dos relés:", error);
            showNotification("Erro de rede ao buscar status dos disjuntores", "error");
        });
}

// Atualiza os switches individuais quando um grupo é alterado
function updateIndividualSwitchesForGroup(groupId, isChecked) {
    const groupMap = {
        "frente": [1, 2],
        "meio": [3, 4],
        "fundo": [5, 6]
    };
    const relaysInGroup = groupMap[groupId];
    if (relaysInGroup) {
        relaysInGroup.forEach(relayNum => {
            const individualSwitch = document.getElementById(`disjuntor-switch-${relayNum}`);
            if (individualSwitch) {
                individualSwitch.checked = isChecked;
            }
        });
    }
}

// Atualiza o estado dos botões de grupo com base nos individuais
function updateGroupSwitchesState() {
    const groupMap = {
        "frente": [1, 2],
        "meio": [3, 4],
        "fundo": [5, 6]
    };
    for (const groupId in groupMap) {
        const groupSwitch = document.getElementById(`grupo-switch-${groupId}`);
        const relaysInGroup = groupMap[groupId];
        if (groupSwitch && relaysInGroup) {
            // Verifica se TODOS os individuais do grupo estão ligados
            const allOn = relaysInGroup.every(relayNum => {
                const individualSwitch = document.getElementById(`disjuntor-switch-${relayNum}`);
                return individualSwitch && individualSwitch.checked;
            });
            // Verifica se TODOS os individuais do grupo estão desligados
            const allOff = relaysInGroup.every(relayNum => {
                const individualSwitch = document.getElementById(`disjuntor-switch-${relayNum}`);
                return individualSwitch && !individualSwitch.checked;
            });

            // Define o estado do grupo: ligado se todos ligados, desligado se todos desligados
            // Em estado misto, o grupo fica desligado (ou pode-se adicionar estado indeterminado)
            groupSwitch.checked = allOn;

            // Opcional: Adicionar estado visual indeterminado se nem todos on/off
            if (!allOn && !allOff) {
                // groupSwitch.indeterminate = true; // Pode não funcionar bem com switches
            }
        }
    }
}

// --- FIM DAS FUNÇÕES DE CONTROLE DE DISJUNTORES ---

// REMOVIDO: Função antiga de controle de luzes
// function toggleLight(lightId, state) { ... }

// --- FUNÇÕES PARA O PREVIEW DO OBS --- 
function startObsPreviewUpdate() {
    if (obsPreviewInterval) {
        clearInterval(obsPreviewInterval); // Limpa intervalo anterior se existir
    }
    console.log("Iniciando atualização do preview do OBS...");
    updateObsPreview(); // Chama imediatamente a primeira vez
    obsPreviewInterval = setInterval(updateObsPreview, PREVIEW_UPDATE_INTERVAL);
}

function stopObsPreviewUpdate() {
    if (obsPreviewInterval) {
        console.log("Parando atualização do preview do OBS...");
        clearInterval(obsPreviewInterval);
        obsPreviewInterval = null;
    }
}

function updateObsPreview() {
    const imgElement = document.getElementById("obs-preview-image");
    const loadingElement = document.getElementById("obs-preview-loading");
    const errorElement = document.getElementById("obs-preview-error");

    if (!imgElement || !loadingElement || !errorElement) return; // Elementos não encontrados

    errorElement.classList.add("d-none");

    fetch("/api/obs/preview")
        .then(response => response.json())
        .then(data => {
            loadingElement.classList.add("d-none"); // Esconde loading
            if (data.success && data.imageData) {
                imgElement.src = data.imageData; // Atualiza a imagem
                imgElement.classList.remove("d-none");
            } else {
                console.error("Erro ao obter preview:", data.message);
                showPreviewError(data.message || "Falha ao obter imagem");
            }
        })
        .catch(error => {
            console.error("Erro de rede ao obter preview:", error);
            stopObsPreviewUpdate(); // Para de tentar se der erro de rede
            showPreviewError("Erro de rede");
        });
}

function showPreviewError(message) {
    const imgElement = document.getElementById("obs-preview-image");
    const loadingElement = document.getElementById("obs-preview-loading");
    const errorElement = document.getElementById("obs-preview-error");

    if (imgElement) imgElement.classList.add("d-none"); // Esconde imagem
    if (loadingElement) loadingElement.classList.add("d-none"); // Esconde loading
    if (errorElement) {
        errorElement.textContent = `Erro no Preview: ${message}`;
        errorElement.classList.remove("d-none"); // Mostra erro
    }
}
// --- FIM DAS FUNÇÕES DE PREVIEW ---

// Função para mostrar notificações
function showNotification(message, type = "secondary") {
    const toast = document.getElementById("notification-toast");
    const toastMessage = document.getElementById("toast-message");

    if (toast && toastMessage) {
        toastMessage.textContent = message;
        toast.className = "toast"; // Reset classes
        if (type === "error") {
            toast.classList.add("bg-danger", "text-light");
        } else {
            // Usando bg-secondary para manter o padrão visual anterior
            toast.classList.add("bg-secondary", "text-light");
        }
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();
    }
}

