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
    instalacoes_db = await cursor.to_list(length=200)

    instalacoes = []
    for item in instalacoes_db:
        data_inicial = item.get("data_inicial_instalacao")
        data_final = item.get("data_final_instalacao")

        if hasattr(data_inicial, "strftime"):
            data_inicial_fmt = data_inicial.strftime("%d/%m/%Y")
        else:
            data_inicial_fmt = str(data_inicial) if data_inicial else ""

        if hasattr(data_final, "strftime"):
            data_final_fmt = data_final.strftime("%d/%m/%Y")
        else:
            data_final_fmt = str(data_final) if data_final else ""

        if data_inicial and data_final:
            status = "Concluído"
            status_classe = "status-concluido"
        elif data_inicial:
            status = "Aberto"
            status_classe = "status-aberto"
        else:
            status = "Pendente"
            status_classe = "status-pendente"

        instalacoes.append({
            "qr_id": item.get("qr_id", ""),
            "cliente": item.get("cliente", ""),
            "produto": item.get("produto", ""),
            "projetista": item.get("projetista", "") or "",
            "data_inicial_fmt": data_inicial_fmt,
            "data_final_fmt": data_final_fmt,
            "status": status,
            "status_classe": status_classe
        })

    return templates.TemplateResponse("historico.html", {
        "request": request,
        "usuario": usuario,
        "instalacoes": instalacoes,
        "busca": busca
    })