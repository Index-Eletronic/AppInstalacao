from datetime import datetime

from bson import ObjectId
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import db
from .auth import gerar_hash_senha, verificar_senha, criar_token, ler_token
from .utils import limpar_cpf, parse_date

app = FastAPI(title="Sistema de Instalação")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


async def buscar_usuario_logado(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = ler_token(token)
    if not payload:
        return None

    usuario_id = payload.get("sub")
    if not usuario_id:
        return None

    try:
        usuario = await db.usuarios.find_one({"_id": ObjectId(usuario_id)})
        return usuario
    except Exception:
        return None


@app.on_event("startup")
async def startup():
    await db.usuarios.create_index("cpf", unique=True)
    await db.instalacoes.create_index("usuario_id")
    await db.instalacoes.create_index("qr_id")
    await db.instalacoes.create_index("cliente")
    await db.funcionarios_autorizados.create_index("cpf", unique=True)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    usuario = await buscar_usuario_logado(request)
    if usuario:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def tela_login(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "erro": ""
    })


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    cpf: str = Form(...),
    senha: str = Form(...)
):
    cpf = limpar_cpf(cpf)

    usuario = await db.usuarios.find_one({"cpf": cpf})

    if not usuario or not verificar_senha(senha, usuario["senha_hash"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "erro": "CPF ou senha inválidos."
        })

    token = criar_token({
        "sub": str(usuario["_id"]),
        "cpf": usuario["cpf"]
    })

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )
    return response


@app.get("/cadastro", response_class=HTMLResponse)
async def tela_cadastro(request: Request):
    return templates.TemplateResponse("cadastro.html", {
        "request": request,
        "erro": "",
        "sucesso": "",
        "funcionario_nome": ""
    })


@app.get("/funcionarios/consultar-cpf/{cpf}")
async def consultar_cpf_autorizado(cpf: str):
    cpf = limpar_cpf(cpf)

    funcionario = await db.funcionarios_autorizados.find_one({"cpf": cpf})
    if not funcionario:
        return {
            "ok": True,
            "encontrado": False,
            "ativo": False,
            "nome": "",
            "mensagem": "CPF não autorizado para cadastro."
        }

    if not funcionario.get("ativo", False):
        return {
            "ok": True,
            "encontrado": True,
            "ativo": False,
            "nome": funcionario.get("nome", ""),
            "mensagem": "Funcionário encontrado, mas está inativo."
        }

    return {
        "ok": True,
        "encontrado": True,
        "ativo": True,
        "nome": funcionario.get("nome", ""),
        "mensagem": f"Funcionário encontrado: {funcionario.get('nome', '')}"
    }


@app.post("/cadastro", response_class=HTMLResponse)
async def cadastrar(
    request: Request,
    cpf: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...)
):
    cpf = limpar_cpf(cpf)

    if not cpf or not senha.strip() or not confirmar_senha.strip():
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "Preencha todos os campos.",
            "sucesso": "",
            "funcionario_nome": ""
        })

    if senha != confirmar_senha:
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "As senhas não conferem.",
            "sucesso": "",
            "funcionario_nome": ""
        })

    if len(senha.encode("utf-8")) > 72:
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "A senha deve ter no máximo 72 bytes.",
            "sucesso": "",
            "funcionario_nome": ""
        })

    funcionario = await db.funcionarios_autorizados.find_one({"cpf": cpf})
    if not funcionario:
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "CPF não autorizado para cadastro.",
            "sucesso": "",
            "funcionario_nome": ""
        })

    if not funcionario.get("ativo", False):
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "Este funcionário está inativo e não pode criar acesso.",
            "sucesso": "",
            "funcionario_nome": funcionario.get("nome", "")
        })

    existente = await db.usuarios.find_one({"cpf": cpf})
    if existente:
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "Este CPF já possui cadastro no sistema.",
            "sucesso": "",
            "funcionario_nome": funcionario.get("nome", "")
        })

    try:
        usuario = {
            "nome": funcionario.get("nome", "").strip(),
            "cpf": cpf,
            "senha_hash": gerar_hash_senha(senha),
            "criado_em": datetime.utcnow()
        }

        await db.usuarios.insert_one(usuario)

        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "",
            "sucesso": f"Cadastro realizado com sucesso para {usuario['nome']}.",
            "funcionario_nome": usuario["nome"]
        })

    except Exception as e:
        print("ERRO NO CADASTRO:", e)
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": f"Erro ao cadastrar: {e}",
            "sucesso": "",
            "funcionario_nome": funcionario.get("nome", "")
        })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    usuario = await buscar_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": usuario,
        "mensagem": "",
        "erro": "",
        "limpar_formulario": False
    })


@app.get("/instalacoes/consulta-qr/{qr_id}")
async def consultar_qr(qr_id: str, request: Request):
    usuario = await buscar_usuario_logado(request)
    if not usuario:
        return JSONResponse(
            status_code=401,
            content={"ok": False, "erro": "Usuário não autenticado."}
        )

    registro = await db.instalacoes.find_one({"qr_id": qr_id.strip()})

    if not registro:
        return {
            "ok": True,
            "existe": False,
            "status": "novo",
            "mensagem": "NOVO ID. Ao salvar, esta data será registrada como data inicial.",
            "aviso_titulo": "NOVO ID",
            "aviso_tipo": "novo",
            "data_inicial_instalacao": None,
            "data_final_instalacao": None
        }

    data_inicial = registro.get("data_inicial_instalacao")
    data_final = registro.get("data_final_instalacao")

    if data_inicial and not data_final:
        return {
            "ok": True,
            "existe": True,
            "status": "aguardando_data_final",
            "mensagem": "Este ID já possui data inicial. Ao salvar, a data informada será registrada como data final.",
            "aviso_titulo": "AGUARDANDO DATA FINAL",
            "aviso_tipo": "aberto",
            "data_inicial_instalacao": data_inicial.strftime("%Y-%m-%d") if data_inicial else None,
            "data_final_instalacao": None
        }

    if data_inicial and data_final:
        return {
            "ok": True,
            "existe": True,
            "status": "concluido",
            "mensagem": "Este ID já possui data inicial e data final salvas.",
            "aviso_titulo": "CONCLUÍDO",
            "aviso_tipo": "concluido",
            "data_inicial_instalacao": data_inicial.strftime("%Y-%m-%d") if data_inicial else None,
            "data_final_instalacao": data_final.strftime("%Y-%m-%d") if data_final else None
        }

    return {
        "ok": True,
        "existe": True,
        "status": "aguardando_data_inicial",
        "mensagem": "Este ID existe, mas ainda não possui data inicial.",
        "aviso_titulo": "AGUARDANDO DATA INICIAL",
        "aviso_tipo": "novo",
        "data_inicial_instalacao": None,
        "data_final_instalacao": None
    }


@app.post("/instalacoes", response_class=HTMLResponse)
async def salvar_instalacao(
    request: Request,
    qr_id: str = Form(...),
    data_qr: str = Form(""),
    cliente: str = Form(...),
    produto: str = Form(...),
    projetista: str = Form(""),
    data_instalacao: str = Form(...)
):
    usuario = await buscar_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    try:
        if not data_instalacao:
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "usuario": usuario,
                "mensagem": "",
                "erro": "Preencha a data da instalação.",
                "limpar_formulario": False
            })

        dt_instalacao = parse_date(data_instalacao)

        registro_existente = await db.instalacoes.find_one({
            "qr_id": qr_id.strip()
        })

        if registro_existente:
            update_data = {}

            if not registro_existente.get("data_inicial_instalacao"):
                update_data["data_inicial_instalacao"] = dt_instalacao
                update_data["instalador_inicial_cpf"] = usuario["cpf"]
                update_data["instalador_inicial_nome"] = usuario["nome"]
            elif not registro_existente.get("data_final_instalacao"):
                if dt_instalacao < registro_existente["data_inicial_instalacao"]:
                    return templates.TemplateResponse("dashboard.html", {
                        "request": request,
                        "usuario": usuario,
                        "mensagem": "",
                        "erro": "A data final não pode ser menor que a data inicial.",
                        "limpar_formulario": False
                    })
                update_data["data_final_instalacao"] = dt_instalacao
                update_data["instalador_final_cpf"] = usuario["cpf"]
                update_data["instalador_final_nome"] = usuario["nome"]
            else:
                return templates.TemplateResponse("dashboard.html", {
                    "request": request,
                    "usuario": usuario,
                    "mensagem": "",
                    "erro": "Este QR já possui data inicial e data final salvas.",
                    "limpar_formulario": False
                })

            await db.instalacoes.update_one(
                {"_id": registro_existente["_id"]},
                {"$set": update_data}
            )

            mensagem = "Data da instalação atualizada com sucesso."
        else:
            instalacao = {
                "usuario_id": str(usuario["_id"]),
                "usuario_nome": usuario["nome"],
                "qr_id": qr_id.strip(),
                "data_qr": parse_date(data_qr) if data_qr else None,
                "cliente": cliente.strip(),
                "produto": produto.strip(),
                "projetista": projetista.strip() or None,
                "data_inicial_instalacao": dt_instalacao,
                "data_final_instalacao": None,
                "instalador_inicial_cpf": usuario["cpf"],
                "instalador_inicial_nome": usuario["nome"],
                "instalador_final_cpf": None,
                "instalador_final_nome": None,
                "criado_em": datetime.utcnow()
            }

            await db.instalacoes.insert_one(instalacao)
            mensagem = "Instalação salva com sucesso."

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "usuario": usuario,
            "mensagem": mensagem,
            "erro": "",
            "limpar_formulario": True
        })

    except Exception as e:
        print("ERRO AO SALVAR INSTALACAO:", e)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "usuario": usuario,
            "mensagem": "",
            "erro": "Erro ao salvar a instalação.",
            "limpar_formulario": False
        })


@app.get("/historico", response_class=HTMLResponse)
async def historico(
    request: Request,
    busca: str = ""
):
    usuario = await buscar_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    filtro = {}

    busca = busca.strip()
    if busca:
        filtro["$or"] = [
            {"cliente": {"$regex": busca, "$options": "i"}},
            {"qr_id": {"$regex": busca, "$options": "i"}}
        ]

    cursor = db.instalacoes.find(filtro).sort("criado_em", -1)
    instalacoes = await cursor.to_list(length=200)

    return templates.TemplateResponse("historico.html", {
        "request": request,
        "usuario": usuario,
        "instalacoes": instalacoes,
        "busca": busca
    })


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response