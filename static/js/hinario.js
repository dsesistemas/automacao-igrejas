// JavaScript para a página do hinário
let obsPreviewInterval = null; // Variável para controlar o intervalo de atualização
const PREVIEW_UPDATE_INTERVAL = 2000; // Intervalo em milissegundos (2 segundos)

document.addEventListener("DOMContentLoaded", function() {
    // Formulário de pesquisa
    const searchForm = document.getElementById("search-form");
    const searchInput = document.getElementById("search-input");
    const searchResults = document.getElementById("search-results");

    if (searchForm) {
        searchForm.addEventListener("submit", function(e) {
            e.preventDefault();
            const searchTerm = searchInput.value.trim();
            
            if (searchTerm.length > 0) {
                searchSongs(searchTerm);
            }
        });
    }

    // --- INICIAR ATUALIZAÇÃO DO PREVIEW --- 
    checkOBSStatus(); // Verifica status antes de iniciar
    startObsPreviewUpdate();
    // --- FIM --- 
    
    // Verificar status a cada 30 segundos
    setInterval(checkOBSStatus, 30000);
});

// Função para pesquisar músicas
function searchSongs(searchTerm) {
    const searchResults = document.getElementById("search-results");
    searchResults.innerHTML = 
        `<div class="text-center">
            <div class="spinner-border text-secondary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
        </div>`;
    
    fetch("/api/search_songs", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `search_term=${encodeURIComponent(searchTerm)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.length === 0) {
            searchResults.innerHTML = 
                `<div class="text-center text-muted">
                    <p>Nenhuma música encontrada</p>
                </div>`;
            return;
        }
        let resultsHtml = "";
        data.forEach(song => {
            const formattedContent = song.content.replace(/;\s*/g, "<br>");
            resultsHtml += 
                `<div class="song-item mb-4 pb-3 border-bottom">
                    <div class="fw-bold">TÍTULO: ${song.title}</div>
                    <div class="text-muted small">CATEGORIAS: ${song.categories}</div>
                    <div class="mt-2 song-content">${formattedContent}</div> 
                </div>`;
        });
        searchResults.innerHTML = resultsHtml;
        showNotification(`${data.length} música(s) encontrada(s)`);
    })
    .catch(error => {
        console.error("Erro na pesquisa:", error);
        searchResults.innerHTML = 
            `<div class="alert alert-danger">
                Erro ao pesquisar músicas. Tente novamente.
            </div>`;
        showNotification("Erro ao pesquisar músicas", "error");
    });
}

// --- FUNÇÕES PARA O PREVIEW DO OBS (COPIADAS DE main.js) --- 
function checkOBSStatus() {
    fetch("/api/obs/status")
        .then(response => response.json())
        .then(data => {
            const statusAlert = document.getElementById("obs-status-alert");
            const statusMessage = document.getElementById("obs-status-message");
            
            if (!statusAlert || !statusMessage) return;

            if (data.status === "connected") {
                statusAlert.className = "alert alert-success";
                statusMessage.textContent = "Conectado ao OBS Studio";
                if (!obsPreviewInterval) {
                    startObsPreviewUpdate();
                }
            } else {
                statusAlert.className = "alert alert-danger";
                statusMessage.textContent = data.message || "Erro desconhecido ao conectar ao OBS";
                stopObsPreviewUpdate();
                showPreviewError("OBS desconectado");
            }
        })
        .catch(error => {
            console.error("Erro ao verificar status:", error);
            const statusAlert = document.getElementById("obs-status-alert");
            const statusMessage = document.getElementById("obs-status-message");
            if (statusAlert && statusMessage) {
                statusAlert.className = "alert alert-danger";
                statusMessage.textContent = "Erro de rede ao verificar status do OBS.";
            }
            stopObsPreviewUpdate();
            showPreviewError("Erro de rede");
        });
}

function startObsPreviewUpdate() {
    if (obsPreviewInterval) {
        clearInterval(obsPreviewInterval);
    }
    console.log("Iniciando atualização do preview do OBS (Hinário)...");
    updateObsPreview();
    obsPreviewInterval = setInterval(updateObsPreview, PREVIEW_UPDATE_INTERVAL);
}

function stopObsPreviewUpdate() {
    if (obsPreviewInterval) {
        console.log("Parando atualização do preview do OBS (Hinário)...");
        clearInterval(obsPreviewInterval);
        obsPreviewInterval = null;
    }
}

function updateObsPreview() {
    const imgElement = document.getElementById("obs-preview-image");
    const loadingElement = document.getElementById("obs-preview-loading");
    const errorElement = document.getElementById("obs-preview-error");

    if (!imgElement || !loadingElement || !errorElement) return;

    errorElement.classList.add("d-none");

    fetch("/api/obs/preview")
        .then(response => response.json())
        .then(data => {
            loadingElement.classList.add("d-none");
            if (data.success && data.imageData) {
                imgElement.src = data.imageData;
                imgElement.classList.remove("d-none");
            } else {
                console.error("Erro ao obter preview:", data.message);
                showPreviewError(data.message || "Falha ao obter imagem");
            }
        })
        .catch(error => {
            console.error("Erro de rede ao obter preview:", error);
            stopObsPreviewUpdate();
            showPreviewError("Erro de rede");
        });
}

function showPreviewError(message) {
    const imgElement = document.getElementById("obs-preview-image");
    const loadingElement = document.getElementById("obs-preview-loading");
    const errorElement = document.getElementById("obs-preview-error");

    if (imgElement) imgElement.classList.add("d-none");
    if (loadingElement) loadingElement.classList.add("d-none");
    if (errorElement) {
        errorElement.textContent = `Erro no Preview: ${message}`;
        errorElement.classList.remove("d-none");
    }
}
// --- FIM DAS FUNÇÕES DE PREVIEW ---

// Função para mostrar notificações
function showNotification(message, type = "info") {
    const toast = document.getElementById("notification-toast");
    const toastMessage = document.getElementById("toast-message");
    
    if (toast && toastMessage) {
        toastMessage.textContent = message;
        toast.className = "toast"; // Reset classes
        if (type === "error") {
            toast.classList.add("bg-danger", "text-light");
        } else {
            toast.classList.add("bg-secondary", "text-light");
        }
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();
    }
}
