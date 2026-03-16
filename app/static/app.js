let html5QrCode = null;
let scannerAtivo = false;

function preencherQR() {
    const campo = document.getElementById("qr_texto");
    if (!campo) return;
    preencherCamposComTextoQR(campo.value);
}

function preencherCamposComTextoQR(texto) {
    const linhas = texto.split("\n");

    const dados = {
        "ID": "",
        "Data": "",
        "Cliente": "",
        "Produto": "",
        "Projetista": ""
    };

    linhas.forEach((linha) => {
        if (linha.includes("=")) {
            const partes = linha.split("=");
            const chave = partes[0].trim();
            const valor = partes.slice(1).join("=").trim();

            if (Object.prototype.hasOwnProperty.call(dados, chave)) {
                dados[chave] = valor;
            }
        }
    });

    const qrId = document.getElementById("qr_id");
    const dataQr = document.getElementById("data_qr");
    const cliente = document.getElementById("cliente");
    const produto = document.getElementById("produto");
    const projetista = document.getElementById("projetista");

    if (qrId) qrId.value = dados["ID"] || "";
    if (dataQr) dataQr.value = normalizarDataParaInput(dados["Data"]);
    if (cliente) cliente.value = dados["Cliente"] || "";
    if (produto) produto.value = dados["Produto"] || "";
    if (projetista) projetista.value = dados["Projetista"] || "";
}

function normalizarDataParaInput(valor) {
    if (!valor) return "";

    if (/^\d{4}-\d{2}-\d{2}$/.test(valor)) {
        return valor;
    }

    if (/^\d{2}\/\d{2}\/\d{4}$/.test(valor)) {
        const [dia, mes, ano] = valor.split("/");
        return `${ano}-${mes}-${dia}`;
    }

    return "";
}

function setScannerStatus(texto, isError = false) {
    const el = document.getElementById("scanner-status");
    if (!el) return;
    el.textContent = texto;
    el.style.color = isError ? "#b91c1c" : "#15803d";
}

async function iniciarScanner() {
    if (scannerAtivo) {
        setScannerStatus("A câmera já está ativa.");
        return;
    }

    if (typeof Html5Qrcode === "undefined") {
        setScannerStatus("Biblioteca do scanner não foi carregada.", true);
        return;
    }

    try {
        html5QrCode = new Html5Qrcode("qr-reader");

        await html5QrCode.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: { width: 250, height: 250 } },
            (decodedText) => {
                const qrTexto = document.getElementById("qr_texto");
                if (qrTexto) qrTexto.value = decodedText;
                preencherCamposComTextoQR(decodedText);
                setScannerStatus("QR lido com sucesso.");
                pararScanner();
            },
            () => {}
        );

        scannerAtivo = true;
        setScannerStatus("Câmera iniciada. Aponte para o QR Code.");
    } catch (error) {
        console.error(error);
        setScannerStatus("Não foi possível iniciar a câmera.", true);
    }
}

async function pararScanner() {
    if (!html5QrCode || !scannerAtivo) return;

    try {
        await html5QrCode.stop();
        await html5QrCode.clear();
    } catch (error) {
        console.error("Erro ao parar scanner:", error);
    } finally {
        scannerAtivo = false;
        html5QrCode = null;
        setScannerStatus("Câmera parada.");
    }
}