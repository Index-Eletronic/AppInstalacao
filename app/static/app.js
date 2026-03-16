let html5QrCode = null;
let scannerAtivo = false;

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

    const qrTexto = document.getElementById("qr_texto");
    const qrId = document.getElementById("qr_id");
    const dataQr = document.getElementById("data_qr");
    const cliente = document.getElementById("cliente");
    const produto = document.getElementById("produto");
    const projetista = document.getElementById("projetista");

    if (qrTexto) qrTexto.value = texto || "";
    if (qrId) qrId.value = dados["ID"] || "";
    if (dataQr) dataQr.value = normalizarDataParaInput(dados["Data"]);
    if (cliente) cliente.value = dados["Cliente"] || "";
    if (produto) produto.value = dados["Produto"] || "";
    if (projetista) projetista.value = dados["Projetista"] || "";

    if (dados["ID"]) {
        consultarQrExistente(dados["ID"]);
    } else {
        limparConsultaQr();
        limparAvisoQr();
    }
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

function atualizarEstadoCampoData(status) {
    const dataInstalacao = document.getElementById("data_instalacao");
    const btnSalvar = document.getElementById("btn-salvar");

    if (!dataInstalacao || !btnSalvar) return;

    if (status === "concluido") {
        dataInstalacao.value = "";
        dataInstalacao.disabled = true;
        btnSalvar.disabled = true;
        btnSalvar.style.opacity = "0.6";
        btnSalvar.style.cursor = "not-allowed";
    } else {
        dataInstalacao.disabled = false;
        btnSalvar.disabled = false;
        btnSalvar.style.opacity = "1";
        btnSalvar.style.cursor = "pointer";
    }
}

function mostrarAvisoQr(titulo, mensagem, tipo) {
    const box = document.getElementById("qr-aviso-box");
    const tituloEl = document.getElementById("qr-aviso-titulo");
    const mensagemEl = document.getElementById("qr-aviso-mensagem");

    if (!box || !tituloEl || !mensagemEl) return;

    box.style.display = "block";
    box.className = "qr-aviso-box";

    if (tipo) {
        box.classList.add(`qr-aviso-${tipo}`);
    }

    tituloEl.textContent = titulo || "";
    mensagemEl.textContent = mensagem || "";
}

function limparAvisoQr() {
    const box = document.getElementById("qr-aviso-box");
    const tituloEl = document.getElementById("qr-aviso-titulo");
    const mensagemEl = document.getElementById("qr-aviso-mensagem");

    if (!box || !tituloEl || !mensagemEl) return;

    box.style.display = "none";
    box.className = "qr-aviso-box";
    tituloEl.textContent = "";
    mensagemEl.textContent = "";
}

function limparConsultaQr() {
    const box = document.getElementById("qr-consulta-box");
    const status = document.getElementById("qr-consulta-status");
    const mensagem = document.getElementById("qr-consulta-mensagem");
    const dataInicial = document.getElementById("qr-data-inicial");
    const dataFinal = document.getElementById("qr-data-final");

    if (box) box.style.display = "none";
    if (status) status.textContent = "";
    if (mensagem) mensagem.textContent = "";
    if (dataInicial) dataInicial.textContent = "-";
    if (dataFinal) dataFinal.textContent = "-";

    atualizarEstadoCampoData("");
}

function limparFormularioPosSalvamento() {
    const qrTexto = document.getElementById("qr_texto");
    const qrId = document.getElementById("qr_id");
    const dataQr = document.getElementById("data_qr");
    const cliente = document.getElementById("cliente");
    const produto = document.getElementById("produto");
    const projetista = document.getElementById("projetista");
    const dataInstalacao = document.getElementById("data_instalacao");

    if (qrTexto) qrTexto.value = "";
    if (qrId) qrId.value = "";
    if (dataQr) dataQr.value = "";
    if (cliente) cliente.value = "";
    if (produto) produto.value = "";
    if (projetista) projetista.value = "";
    if (dataInstalacao) {
        dataInstalacao.value = "";
        dataInstalacao.disabled = false;
    }

    limparConsultaQr();
    limparAvisoQr();
    setScannerStatus("Pronto para o próximo QR.");
}

async function consultarQrExistente(qrId) {
    try {
        const response = await fetch(`/instalacoes/consulta-qr/${encodeURIComponent(qrId)}`, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error("Falha ao consultar o QR.");
        }

        const data = await response.json();

        const box = document.getElementById("qr-consulta-box");
        const status = document.getElementById("qr-consulta-status");
        const mensagem = document.getElementById("qr-consulta-mensagem");
        const dataInicial = document.getElementById("qr-data-inicial");
        const dataFinal = document.getElementById("qr-data-final");

        if (box) box.style.display = "block";
        if (status) status.textContent = data.status || "-";
        if (mensagem) mensagem.textContent = data.mensagem || "";
        if (dataInicial) dataInicial.textContent = data.data_inicial_instalacao || "-";
        if (dataFinal) dataFinal.textContent = data.data_final_instalacao || "-";

        mostrarAvisoQr(data.aviso_titulo, data.mensagem, data.aviso_tipo);
        atualizarEstadoCampoData(data.status || "");
    } catch (error) {
        console.error("Erro ao consultar QR:", error);
        const box = document.getElementById("qr-consulta-box");
        const status = document.getElementById("qr-consulta-status");
        const mensagem = document.getElementById("qr-consulta-mensagem");

        if (box) box.style.display = "block";
        if (status) status.textContent = "erro";
        if (mensagem) mensagem.textContent = "Não foi possível consultar o ID no banco de dados.";

        limparAvisoQr();
        atualizarEstadoCampoData("");
    }
}

async function consultarCpfCadastro() {
    const cpfInput = document.getElementById("cpf_cadastro");
    const box = document.getElementById("cpf-consulta-box");
    const mensagem = document.getElementById("cpf-consulta-mensagem");

    if (!cpfInput || !box || !mensagem) return;

    const cpf = cpfInput.value.replace(/\D/g, "");
    if (!cpf) {
        box.style.display = "none";
        mensagem.textContent = "";
        return;
    }

    try {
        const response = await fetch(`/funcionarios/consultar-cpf/${encodeURIComponent(cpf)}`, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error("Erro ao consultar CPF.");
        }

        const data = await response.json();

        box.style.display = "block";
        box.className = "consulta-box";

        if (data.ativo) {
            box.classList.add("consulta-box-ok");
        } else {
            box.classList.add("consulta-box-erro");
        }

        mensagem.textContent = data.mensagem || "";
    } catch (error) {
        console.error("Erro ao consultar CPF:", error);
        box.style.display = "block";
        box.className = "consulta-box consulta-box-erro";
        mensagem.textContent = "Não foi possível consultar o CPF.";
    }
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

    const qrReader = document.getElementById("qr-reader");
    if (!qrReader) {
        setScannerStatus("Área do leitor não encontrada.", true);
        return;
    }

    try {
        html5QrCode = new Html5Qrcode("qr-reader");

        await html5QrCode.start(
            { facingMode: "environment" },
            {
                fps: 10,
                qrbox: { width: 250, height: 250 }
            },
            (decodedText) => {
                preencherCamposComTextoQR(decodedText);
                setScannerStatus("QR lido com sucesso.");
                pararScanner();
            },
            () => {}
        );

        scannerAtivo = true;
        setScannerStatus("Câmera iniciada. Aponte para o QR Code.");
    } catch (error) {
        console.error("Erro ao iniciar scanner:", error);
        setScannerStatus("Não foi possível iniciar a câmera. Verifique permissão e HTTPS.", true);
    }
}

async function pararScanner() {
    if (!html5QrCode || !scannerAtivo) {
        return;
    }

    try {
        await html5QrCode.stop();
        await html5QrCode.clear();
    } catch (error) {
        console.error("Erro ao parar scanner:", error);
    } finally {
        html5QrCode = null;
        scannerAtivo = false;
        setScannerStatus("Câmera parada.");
    }
}