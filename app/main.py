from datetime import datetime

from bson import ObjectId
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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
        "sucesso": ""
    })


@app.post("/cadastro", response_class=HTMLResponse)
async def cadastrar(
    request: Request,
    nome: str = Form(...),
    cpf: str = Form(...),
    senha: str = Form(...)
):
    cpf = limpar_cpf(cpf)

    if not nome.strip() or not cpf or not senha.strip():
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "Preencha todos os campos.",
            "sucesso": ""
        })

    existente = await db.usuarios.find_one({"cpf": cpf})
    if existente:
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "CPF já cadastrado.",
            "sucesso": ""
        })

    try:
        usuario = {
            "nome": nome.strip(),
            "cpf": cpf,
            "senha_hash": gerar_hash_senha(senha),
            "criado_em": datetime.utcnow()
        }

        await db.usuarios.insert_one(usuario)

        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": "",
            "sucesso": "Cadastro realizado com sucesso."
        })

    except Exception as e:
        print("ERRO NO CADASTRO:", e)
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "erro": f"Erro ao cadastrar: {e}",
            "sucesso": ""
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
        "erro": ""
    })


@app.post("/instalacoes", response_class=HTMLResponse)
async def salvar_instalacao(
    request: Request,
    qr_id: str = Form(...),
    data_qr: str = Form(""),
    cliente: str = Form(...),
    produto: str = Form(...),
    projetista: str = Form(""),
    data_inicial_instalacao: str = Form(""),
    data_final_instalacao: str = Form("")
):
    usuario = await buscar_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    try:
        dt_inicial = parse_date(data_inicial_instalacao) if data_inicial_instalacao else None
        dt_final = parse_date(data_final_instalacao) if data_final_instalacao else None

        if dt_inicial and dt_final and dt_final < dt_inicial:
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "usuario": usuario,
                "mensagem": "",
                "erro": "A data final não pode ser menor que a data inicial."
            })

        instalacao = {
            "usuario_id": str(usuario["_id"]),
            "usuario_nome": usuario["nome"],
            "qr_id": qr_id.strip(),
            "data_qr": parse_date(data_qr) if data_qr else None,
            "cliente": cliente.strip(),
            "produto": produto.strip(),
            "projetista": projetista.strip() or None,
            "data_inicial_instalacao": dt_inicial,
            "data_final_instalacao": dt_final,
            "criado_em": datetime.utcnow()
        }

        await db.instalacoes.insert_one(instalacao)

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "usuario": usuario,
            "mensagem": "Instalação salva com sucesso.",
            "erro": ""
        })

    except Exception as e:
        print("ERRO AO SALVAR INSTALACAO:", e)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "usuario": usuario,
            "mensagem": "",
            "erro": "Erro ao salvar a instalação."
        })


@app.get("/historico", response_class=HTMLResponse)
async def historico(request: Request):
    usuario = await buscar_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    cursor = db.instalacoes.find({
        "usuario_id": str(usuario["_id"])
    }).sort("criado_em", -1)

    instalacoes = await cursor.to_list(length=200)

    return templates.TemplateResponse("historico.html", {
        "request": request,
        "usuario": usuario,
        "instalacoes": instalacoes
    })


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response