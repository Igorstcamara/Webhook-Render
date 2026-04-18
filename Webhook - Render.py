import uvicorn
import json
import asyncio
import base64
from datetime import datetime
from fastapi import FastAPI, Request, Response

# ============================================================
#  CONFIGURACOES -- edite apenas esta secao
# ============================================================

PORTA         = 8000
BASIC_USUARIO = "123"
BASIC_SENHA   = "456"

# ============================================================
#  NAO PRECISA EDITAR ABAIXO DESTA LINHA
# ============================================================

app = FastAPI(title="Webhook Receiver -- Pagar.me")

webhooks_recebidos = []

def decodificar_basic_auth(authorization):
    try:
        tipo, token = authorization.split(" ", 1)
        if tipo.lower() != "basic":
            return None, None
        decoded = base64.b64decode(token).decode("utf-8")
        usuario, senha = decoded.split(":", 1)
        return usuario, senha
    except Exception:
        return None, None

def validar_auth(authorization):
    if not authorization:
        return False
    usuario, senha = decodificar_basic_auth(authorization)
    return usuario == BASIC_USUARIO and senha == BASIC_SENHA

@app.post("/webhook")
async def receber_webhook(request: Request):
    hora          = datetime.now().strftime("%H:%M:%S")
    headers       = dict(request.headers)
    authorization = headers.get("authorization", "")

    print("\n" + "=" * 60)
    print(f"  WEBHOOK RECEBIDO -- {hora}")
    print("=" * 60)

    print("\n  HEADERS:")
    print("-" * 60)
    for chave, valor in headers.items():
        print(f"  {chave}: {valor}")
        if chave.lower() == "authorization" and "basic" in valor.lower():
            usuario, senha = decodificar_basic_auth(valor)
            if usuario:
                print(f"    -> usuario: {usuario}")
                print(f"    -> senha:   {senha}")

    if not validar_auth(authorization):
        print("\n  AUTENTICACAO -- FALHOU")
        print(f"  Esperado:  {BASIC_USUARIO}:{BASIC_SENHA}")
        usuario, senha = decodificar_basic_auth(authorization)
        if usuario:
            print(f"  Recebido:  {usuario}:{senha}")
        print("=" * 60 + "\n")
        return Response(
            content=json.dumps({"erro": "nao autorizado", "motivo": "credenciais invalidas"}),
            status_code=401,
            media_type="application/json"
        )

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    entrada = {
        "hora":    hora,
        "headers": headers,
        "payload": payload,
    }
    webhooks_recebidos.append(entrada)

    print("\n  AUTENTICACAO -- OK")
    print("\n  PAYLOAD:")
    print("-" * 60)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("=" * 60 + "\n")

    return {"status": "recebido"}

@app.get("/historico")
async def historico():
    return {
        "total":    len(webhooks_recebidos),
        "webhooks": webhooks_recebidos,
    }

@app.get("/")
async def raiz():
    return {
        "status":    "online",
        "endpoint":  "/webhook",
        "historico": "/historico",
    }

if __name__ == "__main__":
    print("=" * 60)
    print("  Webhook Receiver -- Pagar.me")
    print("=" * 60)
    print(f"\n  Autenticacao esperada: {BASIC_USUARIO}:{BASIC_SENHA}")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=PORTA, log_level="info")