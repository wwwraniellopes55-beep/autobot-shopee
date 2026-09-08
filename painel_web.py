from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import threading
import time
import os
import requests
import hashlib
import json
import random
import base64

app = FastAPI(title="Shopee AutoBot SaaS")

# ==========================================
# CREDENCIAIS SHOPEE E EVOLUTION API
# ==========================================
SHOPEE_APP_ID = "18380880065"
SHOPEE_SECRET = "42LRGW5UMGFZOF65ZKZOYIV6T7VJ7DX7"

EVO_URL = "http://api.auto-boot.shop:8080"
EVO_KEY = "ShopeeAutoBot2026"
EVO_INSTANCE = "ShopeeBot"
EVO_HEADERS = {"apikey": EVO_KEY, "Content-Type": "application/json"}

estado_robo = {
    "ligado": False,
    "disparos": 0,
    "protecoes": 0,
    "inicio_sessao": 0,
    "logs": ["Sistema Inicializado.", "> Conexão com Evolution API (VPS) Ativa."]
}

def add_log(mensagem):
    hora_atual = time.strftime("%H:%M:%S")
    estado_robo["logs"].append(f"[{hora_atual}] {mensagem}")
    if len(estado_robo["logs"]) > 40:
        estado_robo["logs"].pop(0)

# ==========================================
# INTELIGÊNCIA SHOPEE
# ==========================================
def puxar_shopee(keyword_busca):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    payload_str = json.dumps({"query": f'query {{ productOfferV2(keyword: "{keyword_busca}") {{ nodes {{ productName price priceDiscountRate offerLink imageUrl }} }} }}'})
    timestamp = str(int(time.time()))
    fator = SHOPEE_APP_ID + timestamp + payload_str + SHOPEE_SECRET
    signature = hashlib.sha256(fator.encode('utf-8')).hexdigest()
    headers = {"Content-Type": "application/json", "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"}
    
    try:
        resposta = requests.post(url, headers=headers, data=payload_str)
        dados = resposta.json()
        produto = dados['data']['productOfferV2']['nodes'][0]
        nome_limpo = keyword_busca.replace(" mais vendidos", "").capitalize()
        return {
            "nome": produto.get('productName', f'Achado Exclusivo - {nome_limpo}'),
            "preco": produto.get('price', 0.0),
            "desconto": f"{produto.get('priceDiscountRate', 0)}%",
            "link_afiliado": produto.get('offerLink', 'https://shopee.com.br'),
            "imagem_url": produto.get('imageUrl', '')
        }
    except:
        return {"nome": "🔥 Promoção Relâmpago", "preco": 39.90, "desconto": "Off", "link_afiliado": "https://shopee.com.br", "imagem_url": ""}

def criar_copy(produto):
    saudacoes = ["🚨 *ACHADO IMPERDÍVEL!*", "🔥 *BUG DE PREÇO ENCONTRADO!*", "⚡ *OFERTA RELÂMPAGO!*"]
    return (f"{random.choice(saudacoes)}\n\n📦 *{produto['nome']}*\n\n"
            f"😱 *Por apenas: R$ {produto['preco']}* ({produto['desconto']} OFF!)\n\n"
            f"🛒 *Link oficial com desconto:*\n👉 {produto['link_afiliado']}")

# ==========================================
# MOTORES EVOLUTION API (VPS)
# ==========================================
def motor_conectar():
    if os.path.exists("qrcode.png"):
        os.remove("qrcode.png")
        
    try:
        add_log("Solicitando status à VPS...")
        url_status = f"{EVO_URL}/instance/connectionState/{EVO_INSTANCE}"
        status_req = requests.get(url_status, headers=EVO_HEADERS)
        
        if "open" in status_req.text:
            add_log("✅ O WhatsApp já está conectado e pronto na VPS!")
            return
            
        add_log("Solicitando QR Code para a Evolution API...")
        url_connect = f"{EVO_URL}/instance/connect/{EVO_INSTANCE}"
        res = requests.get(url_connect, headers=EVO_HEADERS)
        dados = res.json()
        
        if "base64" in dados:
            img_data = dados["base64"].split(",")[1]
            with open("qrcode.png", "wb") as f:
                f.write(base64.b64decode(img_data))
            add_log("⚠️ QR Code gerado! Escaneie a imagem no painel.")
        else:
            add_log("Aguardando resposta da VPS...")
            
    except Exception as e:
        add_log(f"Erro na conexão com a VPS: {str(e)}")

def motor_iniciar_disparos(nicho, aleatorio, grupos_str, tempo_base):
    # Recebe os IDs dos grupos (ex: 12036...1@g.us)
    lista_grupos = [g.strip() for g in grupos_str.split(',') if g.strip()]
    if not lista_grupos:
        add_log("ERRO: Nenhum ID de grupo informado!")
        estado_robo["ligado"] = False
        return

    nichos_em_alta = ["Fone Sem Fio", "Smartwatch", "Tênis Masculino", "Moda Feminina"]

    try:
        add_log("Verificando conexão da API antes do disparo...")
        url_status = f"{EVO_URL}/instance/connectionState/{EVO_INSTANCE}"
        status = requests.get(url_status, headers=EVO_HEADERS).json()
        
        if status.get("instance", {}).get("state") != "open":
            add_log("❌ ERRO: O WhatsApp está desconectado na VPS.")
            add_log("⚠️ Por favor, clique em CONECTAR WPP e leia o QR Code.")
            estado_robo["ligado"] = False
            return
            
        add_log("Conexão validada. Iniciando varredura e envios via API...")
        
        while estado_robo["ligado"]:
            nicho_atual = random.choice(nichos_em_alta) if aleatorio else nicho
            add_log(f"Buscando produto na Shopee (Nicho: {nicho_atual})...")
            produto = puxar_shopee(f"{nicho_atual} mais vendidos")
            copy = criar_copy(produto)

            for grupo_jid in lista_grupos:
                if not estado_robo["ligado"]: break
                
                add_log(f"Disparando oferta para o ID: {grupo_jid[:10]}...")
                
                # VERIFICA SE EXISTE IMAGEM PARA MUDAR A ROTA DA API
                if produto.get("imagem_url"):
                    payload = {
                        "number": grupo_jid,
                        "mediatype": "image",
                        "media": produto["imagem_url"],
                        "caption": copy
                    }
                    url_send = f"{EVO_URL}/message/sendMedia/{EVO_INSTANCE}"
                else:
                    payload = {
                        "number": grupo_jid,
                        "options": {
                            "delay": 2000,
                            "presence": "composing",
                            "linkPreview": True
                        },
                        "text": copy
                    }
                    url_send = f"{EVO_URL}/message/sendText/{EVO_INSTANCE}"
                
                try:
                    res = requests.post(url_send, headers=EVO_HEADERS, json=payload, timeout=20)
                    
                    if res.status_code == 201:
                        estado_robo["disparos"] += 1
                        add_log("✅ Oferta com foto entregue com sucesso!")
                    else:
                        add_log(f"❌ Falha no envio. Código: {res.status_code}")
                except Exception as ex:
                    add_log(f"Erro de comunicação: {str(ex)}")
                
                time.sleep(random.uniform(2.5, 4.5)) 
            
            add_log(f"Ciclo concluído. Pausa antiban de {tempo_base}s...")
            for i in range(tempo_base):
                if not estado_robo["ligado"]: break
                time.sleep(1)
                
        add_log("Operação abortada. Motor desligado.")
    except Exception as e:
        add_log(f"ERRO CRÍTICO GLOBAL: {str(e)}")
        estado_robo["ligado"] = False

# ==========================================
# ROTAS DA API FASTAPI
# ==========================================
class DadosDisparo(BaseModel):
    nicho: str
    aleatorio: bool
    grupos: str
    tempo: int

@app.post("/api/conectar")
def api_conectar():
    threading.Thread(target=motor_conectar, daemon=True).start()
    return {"status": "ok"}

@app.get("/api/qrcode")
def get_qr():
    if os.path.exists("qrcode.png"):
        return FileResponse("qrcode.png")
    return {"status": "aguardando"}

@app.post("/api/iniciar")
def api_iniciar(dados: DadosDisparo):
    if estado_robo["ligado"]:
        add_log("⚠️ O motor já está rodando! Clique em ABORTAR primeiro.")
        return {"status": "ocupado"}
        
    estado_robo["ligado"] = True
    estado_robo["inicio_sessao"] = time.time()
    threading.Thread(target=motor_iniciar_disparos, args=(dados.nicho, dados.aleatorio, dados.grupos, dados.tempo), daemon=True).start()
    return {"status": "ok"}

@app.post("/api/abortar")
def api_abortar():
    estado_robo["ligado"] = False
    add_log("Sinal de parada enviado. Encerrando em instantes...")
    return {"status": "ok"}

@app.get("/api/status")
def api_status():
    segundos_ativos = int(time.time() - estado_robo["inicio_sessao"]) if estado_robo["ligado"] else 0
    return {
        "ligado": estado_robo["ligado"],
        "disparos": estado_robo["disparos"],
        "tempo_ativo": segundos_ativos,
        "logs": "\n".join(estado_robo["logs"])
    }

# ==========================================
# FRONTEND RESPONSIVO ULTRA PREMIUM
# ==========================================
@app.get("/", response_class=HTMLResponse)
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SaaS - Shopee AutoBot PRO</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { 
                background-color: #020617; /* Slate 950 */
                color: #e2e8f0; 
                font-family: 'Inter', sans-serif;
                background-image: 
                    radial-gradient(at 0% 0%, rgba(30, 58, 138, 0.15) 0px, transparent 50%), 
                    radial-gradient(at 100% 100%, rgba(15, 23, 42, 0.8) 0px, transparent 50%);
                background-attachment: fixed;
            }
            .panel-card { 
                background: #0f172a; /* Slate 900 */
                border: 1px solid #1e293b; /* Slate 800 */
                box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5); 
            }
            .input-premium { 
                background: #020617; 
                border: 1px solid #334155; 
                border-radius: 12px; 
                color: #f8fafc; 
                padding: 12px 16px; 
                width: 100%; 
                outline: none; 
                transition: all 0.3s ease; 
                font-size: 0.95rem; 
            }
            .input-premium:focus { 
                border-color: #3b82f6; 
                box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1); 
            }
            .terminal-window { 
                background: #000000; 
                color: #10b981; 
                font-family: 'JetBrains Mono', monospace; 
                border: 1px solid #1e293b; 
            }
            ::-webkit-scrollbar { width: 6px; } 
            ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: #475569; }
        </style>
    </head>
    <body class="flex flex-col md:flex-row min-h-screen overflow-y-auto overflow-x-hidden">
        
        <!-- SIDEBAR -->
        <aside class="w-full md:w-80 panel-card p-6 flex flex-col gap-8 relative z-10 md:border-r border-slate-800 md:h-screen">
            <div class="flex items-center gap-3 mb-2 mt-2">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-rose-600 flex items-center justify-center shadow-lg shadow-orange-500/20">
                    <i class="fa-solid fa-robot text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight">AutoBot <span class="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-rose-500">PRO</span></h1>
                    <p class="text-xs text-slate-400 font-medium tracking-wider">TERMINAL DE VENDAS</p>
                </div>
            </div>
            
            <div class="space-y-6">
                <div>
                    <label class="block text-xs font-semibold mb-2 text-slate-400 uppercase tracking-widest">Nicho de Produto</label>
                    <input type="text" id="inp-nicho" value="Tênis" class="input-premium shadow-inner">
                    <label class="flex items-center gap-3 mt-3 cursor-pointer text-sm text-slate-300 hover:text-white transition-colors">
                        <div class="relative flex items-center">
                            <input type="checkbox" id="chk-aleatorio" class="peer sr-only">
                            <div class="w-10 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-orange-500"></div>
                        </div>
                        <span class="font-medium">Modo Aleatório (Em Alta)</span>
                    </label>
                </div>
                <div>
                    <label class="block text-xs font-semibold mb-2 text-slate-400 uppercase tracking-widest">IDs WPP (Multi-Grupos)</label>
                    <input type="text" id="inp-grupos" placeholder="Ex: 12036...1@g.us" class="input-premium shadow-inner font-mono text-sm" value="120363408173427801@g.us">
                </div>
                <div>
                    <label class="block text-xs font-semibold mb-2 text-slate-400 uppercase tracking-widest">Intervalo (Segundos)</label>
                    <input type="number" id="inp-tempo" value="30" class="input-premium shadow-inner">
                </div>
            </div>
            
            <div class="mt-auto pt-6 border-t border-slate-800">
                <p class="text-xs text-slate-500 text-center flex items-center justify-center gap-2">
                    <i class="fa-solid fa-shield-halved"></i> VPS Connection Secured
                </p>
            </div>
        </aside>

        <!-- MAIN CONTENT -->
        <main class="flex-1 p-4 md:p-8 flex flex-col gap-6 relative z-10 w-full bg-[#020617]">
            
            <!-- QR CODE MODAL -->
            <div id="qr-container" class="hidden flex-col items-center justify-center p-8 panel-card rounded-2xl border border-yellow-500/30 shadow-[0_0_40px_rgba(234,179,8,0.1)]">
                <div class="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center mb-4">
                    <i class="fa-solid fa-qrcode text-2xl text-yellow-500 animate-pulse"></i>
                </div>
                <p class="text-white font-semibold mb-6 text-lg text-center">Conexão Necessária</p>
                <div class="bg-white p-3 rounded-xl shadow-xl">
                    <img id="qr-img" src="" class="w-56 h-56 md:w-64 md:h-64 object-contain">
                </div>
                <p class="text-sm text-slate-400 mt-6 text-center bg-slate-800/50 py-2 px-4 rounded-lg">Abra o WhatsApp, vá em "Aparelhos Conectados" e escaneie.</p>
            </div>

            <!-- STATUS DASHBOARD -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Status Motor -->
                <div class="panel-card rounded-2xl p-5 flex items-center gap-4 transition-all">
                    <div id="status-bg" class="w-14 h-14 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
                        <i id="status-icon" class="fa-solid fa-power-off text-2xl text-slate-500"></i>
                    </div>
                    <div>
                        <p class="text-[10px] text-slate-400 uppercase font-bold tracking-widest mb-1">Status do Motor</p>
                        <p id="status-texto" class="text-xl font-bold text-white">STANDBY</p>
                    </div>
                </div>
                
                <!-- Status Disparos -->
                <div class="panel-card rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden">
                    <div class="absolute -right-4 -top-4 w-24 h-24 bg-green-500/10 rounded-full blur-2xl"></div>
                    <div class="w-14 h-14 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center justify-center shrink-0">
                        <i class="fa-solid fa-paper-plane text-2xl text-green-400"></i>
                    </div>
                    <div>
                        <p class="text-[10px] text-slate-400 uppercase font-bold tracking-widest mb-1">Disparos Concluídos</p>
                        <p id="lbl-disparos" class="text-3xl font-bold text-white">0</p>
                    </div>
                </div>

                <!-- Status Uptime -->
                <div class="panel-card rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden">
                    <div class="absolute -right-4 -top-4 w-24 h-24 bg-purple-500/10 rounded-full blur-2xl"></div>
                    <div class="w-14 h-14 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0">
                        <i class="fa-solid fa-clock text-2xl text-purple-400"></i>
                    </div>
                    <div>
                        <p class="text-[10px] text-slate-400 uppercase font-bold tracking-widest mb-1">Tempo Operacional</p>
                        <p id="lbl-tempo" class="text-2xl font-bold text-white font-mono tracking-tight">00:00:00</p>
                    </div>
                </div>
            </div>

            <!-- TERMINAL CONSOLE -->
            <div class="flex-1 flex flex-col panel-card rounded-2xl min-h-[300px] shadow-2xl overflow-hidden">
                <div class="flex items-center justify-between px-5 py-3 bg-[#0a0f1c] border-b border-slate-800">
                    <div class="flex gap-2">
                        <div class="w-3 h-3 rounded-full bg-[#ef4444] shadow-[0_0_5px_#ef4444]"></div>
                        <div class="w-3 h-3 rounded-full bg-[#f59e0b] shadow-[0_0_5px_#f59e0b]"></div>
                        <div class="w-3 h-3 rounded-full bg-[#10b981] shadow-[0_0_5px_#10b981]"></div>
                    </div>
                    <span class="text-xs text-slate-500 font-mono tracking-wider flex items-center gap-2">
                        <i class="fa-solid fa-terminal text-[10px]"></i> console_output (VPS)
                    </span>
                    <div class="w-14"></div> <!-- Spacer for perfect centering -->
                </div>
                <textarea id="caixa-log" class="terminal-window w-full flex-1 p-6 resize-none text-sm focus:outline-none leading-relaxed" readonly></textarea>
            </div>

            <!-- ACTION BUTTONS -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button onclick="conectarApi()" class="group relative bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-blue-500 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-r from-blue-600/0 via-blue-600/10 to-blue-600/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
                    <div class="flex items-center justify-center gap-3 relative z-10">
                        <i class="fa-solid fa-mobile-screen text-blue-400 group-hover:scale-110 transition-transform"></i> CONECTAR WPP
                    </div>
                </button>
                
                <button onclick="iniciarDisparos()" class="group relative bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] transform hover:-translate-y-1">
                    <div class="flex items-center justify-center gap-3">
                        <i class="fa-solid fa-play text-white group-hover:animate-pulse"></i> INICIAR MOTOR
                    </div>
                </button>
                
                <button onclick="abortarTudo()" class="group bg-slate-800 hover:bg-rose-600/20 border border-slate-700 hover:border-rose-500 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 hover:shadow-[0_0_20px_rgba(225,29,72,0.2)]">
                    <div class="flex items-center justify-center gap-3">
                        <i class="fa-solid fa-stop text-rose-500 group-hover:text-rose-400"></i> ABORTAR
                    </div>
                </button>
            </div>
        </main>

        <script>
            async function conectarApi() { 
                document.getElementById('qr-container').classList.remove('hidden');
                document.getElementById('qr-img').src = "";
                await fetch('/api/conectar', { method: 'POST' }); 
                
                let tentativas = 0;
                let qrInterval = setInterval(async () => {
                    tentativas++;
                    const res = await fetch('/api/qrcode');
                    if(res.headers.get('content-type') && res.headers.get('content-type').includes('image')) {
                        document.getElementById('qr-img').src = '/api/qrcode?' + new Date().getTime();
                        clearInterval(qrInterval);
                        setTimeout(() => { document.getElementById('qr-container').classList.add('hidden'); }, 30000);
                    }
                    if(tentativas > 25) { clearInterval(qrInterval); document.getElementById('qr-container').classList.add('hidden'); }
                }, 2000);
            }
            
            async function abortarTudo() { await fetch('/api/abortar', { method: 'POST' }); }
            
            async function iniciarDisparos() {
                const n = document.getElementById('inp-nicho').value;
                const a = document.getElementById('chk-aleatorio').checked;
                const g = document.getElementById('inp-grupos').value;
                const t = parseInt(document.getElementById('inp-tempo').value);
                await fetch('/api/iniciar', { 
                    method: 'POST', headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify({ nicho: n, aleatorio: a, grupos: g, tempo: t }) 
                });
            }

            function formatarTempo(s) {
                const h = Math.floor(s / 3600).toString().padStart(2, '0');
                const m = Math.floor((s % 3600) / 60).toString().padStart(2, '0');
                const sec = (s % 60).toString().padStart(2, '0');
                return `${h}:${m}:${sec}`;
            }

            setInterval(async () => {
                try {
                    const res = await fetch('/api/status');
                    const dados = await res.json();
                    
                    document.getElementById('lbl-disparos').innerText = dados.disparos;
                    document.getElementById('lbl-tempo').innerText = formatarTempo(dados.tempo_ativo);
                    
                    const logBox = document.getElementById('caixa-log');
                    if(logBox.value !== dados.logs) {
                        logBox.value = dados.logs;
                        logBox.scrollTop = logBox.scrollHeight;
                    }
                    
                    const icon = document.getElementById('status-icon');
                    const bg = document.getElementById('status-bg');
                    const txt = document.getElementById('status-texto');
                    
                    if(dados.ligado) {
                        bg.className = "w-14 h-14 rounded-xl bg-green-500/20 border border-green-500/40 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(34,197,94,0.3)] animate-pulse";
                        icon.className = "fa-solid fa-satellite-dish text-2xl text-green-400";
                        txt.className = "text-xl font-bold text-white drop-shadow-[0_0_8px_rgba(34,197,94,0.8)]";
                        txt.innerText = "ONLINE";
                    } else {
                        bg.className = "w-14 h-14 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700";
                        icon.className = "fa-solid fa-power-off text-2xl text-slate-500";
                        txt.className = "text-xl font-bold text-slate-300";
                        txt.innerText = "STANDBY";
                    }
                } catch (e) {}
            }, 1000);
        </script>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
