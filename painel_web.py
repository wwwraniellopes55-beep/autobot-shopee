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

app = FastAPI(title="Shopee AutoBot SaaS PRO")

# ==========================================
# GERENCIAMENTO DE CONFIGURAÇÕES (JSON)
# ==========================================
ARQUIVO_CONFIG = "config.json"

def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "shopee_id": "", "shopee_secret": "", "grupos": "", 
        "nicho": "Tênis", "tempo": 30, "aleatorio": False
    }

def salvar_config(dados):
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

# ==========================================
# CREDENCIAIS FIXAS EVOLUTION API (VPS)
# ==========================================
EVO_URL = "http://api.auto-boot.shop:8080"
EVO_KEY = "ShopeeAutoBot2026"
EVO_INSTANCE = "ShopeeBot"
EVO_HEADERS = {"apikey": EVO_KEY, "Content-Type": "application/json"}

estado_robo = {
    "ligado": False,
    "disparos": 0,
    "inicio_sessao": 0,
    "proximo_disparo": 0,
    "acao_atual": "INATIVO",
    "produtos_enviados": [], # MEMÓRIA ANTI-REPETIÇÃO
    "logs": ["Terminal Inicializado.", "> Cofre JSON carregado.", "> Conexão VPS pronta."]
}

def add_log(mensagem):
    hora_atual = time.strftime("%H:%M:%S")
    estado_robo["logs"].append(f"[{hora_atual}] {mensagem}")
    if len(estado_robo["logs"]) > 40:
        estado_robo["logs"].pop(0)

# ==========================================
# INTELIGÊNCIA SHOPEE (Com Memória)
# ==========================================
def puxar_shopee(keyword_busca):
    config = carregar_config()
    app_id = config.get("shopee_id", "")
    secret = config.get("shopee_secret", "")
    
    if not app_id or not secret:
        add_log("❌ ERRO: Credenciais da Shopee ausentes. Configure no painel.")
        return None

    url = "https://open-api.affiliate.shopee.com.br/graphql"
    payload_str = json.dumps({"query": f'query {{ productOfferV2(keyword: "{keyword_busca}") {{ nodes {{ productName price priceDiscountRate offerLink imageUrl }} }} }}'})
    timestamp = str(int(time.time()))
    fator = app_id + timestamp + payload_str + secret
    signature = hashlib.sha256(fator.encode('utf-8')).hexdigest()
    headers = {"Content-Type": "application/json", "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"}
    
    try:
        resposta = requests.post(url, headers=headers, data=payload_str)
        dados = resposta.json()
        nodes = dados['data']['productOfferV2']['nodes']
        
        produto_selecionado = None
        
        # FILTRO ANTI-REPETIÇÃO: Procura a primeira oferta que ainda não foi enviada hoje
        for node in nodes:
            nome_oferta = node.get('productName', '')
            if nome_oferta not in estado_robo["produtos_enviados"]:
                produto_selecionado = node
                estado_robo["produtos_enviados"].append(nome_oferta)
                break
                
        if not produto_selecionado:
            add_log("⚠️ Todas as ofertas do topo já foram enviadas. Trocando alvo...")
            return None

        nome_limpo = keyword_busca.replace(" mais vendidos", "").capitalize()
        return {
            "nome": produto_selecionado.get('productName', f'Achado - {nome_limpo}'),
            "preco": produto_selecionado.get('price', 0.0),
            "desconto": f"{produto_selecionado.get('priceDiscountRate', 0)}%",
            "link_afiliado": produto_selecionado.get('offerLink', 'https://shopee.com.br'),
            "imagem_url": produto_selecionado.get('imageUrl', '')
        }
    except Exception as e:
        add_log(f"Erro ao buscar na Shopee: {str(e)}")
        return None

def criar_copy(produto):
    saudacoes = ["🚨 *ACHADO IMPERDÍVEL!*", "🔥 *BUG DE PREÇO ENCONTRADO!*", "⚡ *OFERTA RELÂMPAGO!*"]
    return (f"{random.choice(saudacoes)}\n\n📦 *{produto['nome']}*\n\n"
            f"😱 *Por apenas: R$ {produto['preco']}* ({produto['desconto']} OFF!)\n\n"
            f"🛒 *Link oficial com desconto:*\n👉 {produto['link_afiliado']}")

# ==========================================
# MOTOR BLINDADO EVOLUTION API
# ==========================================
def motor_conectar():
    if os.path.exists("qrcode.png"): os.remove("qrcode.png")
    try:
        add_log("Solicitando status à VPS...")
        status_req = requests.get(f"{EVO_URL}/instance/connectionState/{EVO_INSTANCE}", headers=EVO_HEADERS)
        if "open" in status_req.text:
            add_log("✅ O WhatsApp já está conectado e pronto na VPS!")
            return
            
        add_log("Solicitando QR Code...")
        res = requests.get(f"{EVO_URL}/instance/connect/{EVO_INSTANCE}", headers=EVO_HEADERS).json()
        if "base64" in res:
            with open("qrcode.png", "wb") as f:
                f.write(base64.b64decode(res["base64"].split(",")[1]))
            add_log("⚠️ QR Code gerado! Escaneie no painel.")
    except Exception as e:
        add_log(f"Erro na VPS: {str(e)}")

def motor_iniciar_disparos():
    config = carregar_config()
    lista_grupos = [g.strip() for g in config.get("grupos", "").split(',') if g.strip()]
    
    if not lista_grupos:
        add_log("ERRO: Nenhum ID de grupo informado!")
        estado_robo["ligado"] = False
        return

    try:
        if requests.get(f"{EVO_URL}/instance/connectionState/{EVO_INSTANCE}", headers=EVO_HEADERS).json().get("instance", {}).get("state") != "open":
            add_log("❌ ERRO: WhatsApp desconectado. Leia o QR Code.")
            estado_robo["ligado"] = False
            return
            
        while estado_robo["ligado"]:
            estado_robo["acao_atual"] = "BUSCANDO OFERTA..."
            nicho_atual = random.choice(["Fone Sem Fio", "Smartwatch", "Tênis", "Moda"]) if config["aleatorio"] else config["nicho"]
            produto = puxar_shopee(f"{nicho_atual} mais vendidos")
            
            if not produto: 
                # Se não achar nada novo, espera 5s e tenta outro nicho/ciclo
                time.sleep(5)
                continue
                
            copy = criar_copy(produto)

            for grupo_jid in lista_grupos:
                if not estado_robo["ligado"]: break
                
                estado_robo["acao_atual"] = "DIGITANDO NO WPP..."
                add_log(f"Simulando digitação para o ID: {grupo_jid[:10]}...")
                
                opcoes_delay = {"delay": 6000, "presence": "composing", "linkPreview": True}
                
                if produto.get("imagem_url"):
                    payload = {"number": grupo_jid, "mediatype": "image", "media": produto["imagem_url"], "caption": copy, "options": opcoes_delay}
                    url_send = f"{EVO_URL}/message/sendMedia/{EVO_INSTANCE}"
                else:
                    payload = {"number": grupo_jid, "options": opcoes_delay, "text": copy}
                    url_send = f"{EVO_URL}/message/sendText/{EVO_INSTANCE}"
                
                try:
                    res = requests.post(url_send, headers=EVO_HEADERS, json=payload, timeout=20)
                    if res.status_code == 201:
                        estado_robo["disparos"] += 1
                        add_log("✅ Oferta entregue com sucesso!")
                except Exception as ex:
                    add_log(f"Erro: {str(ex)}")
                
                time.sleep(3) 
            
            estado_robo["acao_atual"] = "AGUARDANDO INTERVALO"
            estado_robo["proximo_disparo"] = time.time() + config["tempo"]
            
            for _ in range(config["tempo"]):
                if not estado_robo["ligado"]: break
                time.sleep(1)
                
        estado_robo["acao_atual"] = "INATIVO"
    except Exception as e:
        add_log(f"ERRO CRÍTICO: {str(e)}")
        estado_robo["ligado"] = False
        estado_robo["acao_atual"] = "ERRO"

# ==========================================
# ROTAS FASTAPI
# ==========================================
@app.get("/api/config")
def get_config(): return carregar_config()

@app.post("/api/config")
def post_config(dados: dict):
    salvar_config(dados)
    return {"status": "salvo"}

@app.post("/api/conectar")
def api_conectar():
    threading.Thread(target=motor_conectar, daemon=True).start()
    return {"status": "ok"}

@app.get("/api/qrcode")
def get_qr():
    if os.path.exists("qrcode.png"): return FileResponse("qrcode.png")
    return {"status": "aguardando"}

@app.post("/api/iniciar")
def api_iniciar():
    if not estado_robo["ligado"]:
        estado_robo["ligado"] = True
        estado_robo["inicio_sessao"] = time.time()
        estado_robo["produtos_enviados"] = [] # ZERA A MEMÓRIA AO INICIAR A SESSÃO
        threading.Thread(target=motor_iniciar_disparos, daemon=True).start()
    return {"status": "ok"}

@app.post("/api/abortar")
def api_abortar():
    estado_robo["ligado"] = False
    estado_robo["proximo_disparo"] = 0
    estado_robo["acao_atual"] = "PARANDO..."
    return {"status": "ok"}

@app.get("/api/status")
def api_status():
    faltam = int(estado_robo["proximo_disparo"] - time.time())
    return {
        "ligado": estado_robo["ligado"],
        "disparos": estado_robo["disparos"],
        "acao": estado_robo["acao_atual"],
        "cronometro": faltam if faltam > 0 and estado_robo["ligado"] else 0,
        "logs": "\n".join(estado_robo["logs"])
    }

# ==========================================
# FRONTEND NEO-GLASSMORPHISM
# ==========================================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Sniper PRO - Automação Shopee</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: #050505; color: #fff; font-family: 'Poppins', sans-serif; overflow-x: hidden; }
            .bg-grid { background-image: linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 40px 40px; }
            .glow-card { background: rgba(15, 15, 20, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; }
            .input-neo { background: #0a0a0c; border: 1px solid #27272a; border-radius: 12px; color: #e4e4e7; padding: 14px 16px; width: 100%; transition: 0.3s; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5); }
            .input-neo:focus { border-color: #06b6d4; outline: none; box-shadow: 0 0 15px rgba(6, 182, 212, 0.2); }
            .term-font { font-family: 'Fira Code', monospace; }
            .text-cyan-glow { text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }
            /* Esconder setas dos inputs numéricos */
            input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
        </style>
    </head>
    <body class="bg-grid min-h-screen p-4 md:p-8 flex flex-col md:flex-row gap-6 relative">
        
        <!-- Efeitos de Luz de Fundo -->
        <div class="absolute top-0 left-1/4 w-96 h-96 bg-cyan-600/20 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-fuchsia-600/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

        <!-- PAINEL DE CONFIGURAÇÕES -->
        <aside class="w-full md:w-[350px] glow-card p-6 flex flex-col relative z-10 shadow-2xl">
            <div class="flex items-center gap-4 mb-8">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                    <i class="fa-solid fa-crosshairs text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-bold tracking-tight text-white">Sniper <span class="text-cyan-400">PRO</span></h1>
                    <p class="text-[10px] text-zinc-400 font-semibold tracking-[0.2em] uppercase">Módulo Afiliado</p>
                </div>
            </div>

            <div class="space-y-5 flex-1 overflow-y-auto pr-2">
                <div>
                    <label class="block text-xs font-semibold mb-2 text-zinc-400 uppercase tracking-widest"><i class="fa-solid fa-key text-cyan-400 mr-2"></i>Shopee App ID</label>
                    <input type="password" id="shopee_id" placeholder="••••••••••••••" class="input-neo text-sm">
                </div>
                <div>
                    <label class="block text-xs font-semibold mb-2 text-zinc-400 uppercase tracking-widest"><i class="fa-solid fa-user-secret text-fuchsia-400 mr-2"></i>Shopee Secret</label>
                    <input type="password" id="shopee_secret" placeholder="••••••••••••••" class="input-neo text-sm">
                </div>
                <div class="h-px w-full bg-zinc-800 my-4"></div>
                <div>
                    <label class="block text-xs font-semibold mb-2 text-zinc-400 uppercase tracking-widest">Nicho Estratégico</label>
                    <input type="text" id="nicho" class="input-neo text-sm">
                    <label class="flex items-center gap-3 mt-3 cursor-pointer group">
                        <div class="relative">
                            <input type="checkbox" id="aleatorio" class="peer sr-only">
                            <div class="w-11 h-6 bg-zinc-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-zinc-300 after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
                        </div>
                        <span class="text-xs text-zinc-400 font-medium group-hover:text-white transition">Girar Nichos em Alta</span>
                    </label>
                </div>
                <div>
                    <label class="block text-xs font-semibold mb-2 text-zinc-400 uppercase tracking-widest">IDs Alvo (WhatsApp)</label>
                    <input type="text" id="grupos" placeholder="12036...@g.us" class="input-neo term-font text-xs">
                </div>
                <div>
                    <label class="block text-xs font-semibold mb-2 text-zinc-400 uppercase tracking-widest">Atraso / Delay (Segundos)</label>
                    <div class="relative">
                        <i class="fa-solid fa-stopwatch absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500"></i>
                        <input type="number" id="tempo" class="input-neo pl-10 text-lg font-semibold">
                    </div>
                </div>
            </div>

            <button onclick="salvarConfig()" id="btn-salvar" class="mt-6 w-full bg-zinc-800 hover:bg-cyan-600 border border-zinc-700 hover:border-cyan-400 text-white font-semibold py-3 rounded-xl transition-all duration-300 flex items-center justify-center gap-2">
                <i class="fa-regular fa-floppy-disk"></i> Salvar Cofre
            </button>
        </aside>

        <!-- DASHBOARD CENTRAL -->
        <main class="flex-1 flex flex-col gap-6 relative z-10 w-full">
            
            <!-- Modal QR -->
            <div id="qr-container" class="hidden absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center rounded-2xl">
                <div class="bg-zinc-900 border border-zinc-700 p-8 rounded-3xl text-center shadow-2xl flex flex-col items-center">
                    <h2 class="text-xl font-bold text-white mb-2">Conecte o Dispositivo</h2>
                    <p class="text-sm text-zinc-400 mb-6">Escaneie via WhatsApp para vincular a VPS</p>
                    <div class="bg-white p-3 rounded-xl">
                        <img id="qr-img" src="" class="w-64 h-64 object-contain">
                    </div>
                    <button onclick="document.getElementById('qr-container').classList.add('hidden')" class="mt-6 text-zinc-400 hover:text-white text-sm">Fechar Janela</button>
                </div>
            </div>

            <!-- HUD de Operação -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Status -->
                <div class="glow-card p-6 flex flex-col justify-center relative overflow-hidden group">
                    <div class="absolute -right-10 -bottom-10 opacity-5 group-hover:scale-110 transition-transform"><i class="fa-solid fa-microchip text-9xl"></i></div>
                    <p class="text-[10px] text-zinc-400 font-bold tracking-widest uppercase mb-1">Processo Atual</p>
                    <p id="lbl-acao" class="text-xl font-bold text-white text-cyan-glow">INATIVO</p>
                </div>
                
                <!-- Cronômetro Real -->
                <div class="glow-card p-6 flex flex-col justify-center items-center relative border-b-4 border-b-cyan-500">
                    <p class="text-[10px] text-cyan-400 font-bold tracking-widest uppercase mb-1"><i class="fa-solid fa-clock-rotate-left mr-1"></i>Próximo Disparo Em</p>
                    <p id="lbl-cronometro" class="term-font text-4xl font-light text-white tracking-wider">00:00</p>
                </div>

                <!-- Disparos -->
                <div class="glow-card p-6 flex flex-col justify-center items-end relative">
                    <p class="text-[10px] text-fuchsia-400 font-bold tracking-widest uppercase mb-1">Cargas Entregues</p>
                    <div class="flex items-baseline gap-2">
                        <p id="lbl-disparos" class="term-font text-4xl font-bold text-white">0</p>
                        <span class="text-zinc-500 text-sm">msgs</span>
                    </div>
                </div>
            </div>

            <!-- Terminal Root -->
            <div class="flex-1 glow-card flex flex-col min-h-[300px] overflow-hidden">
                <div class="bg-black/50 px-4 py-3 border-b border-zinc-800 flex items-center gap-4">
                    <div class="flex gap-2">
                        <div class="w-3 h-3 rounded-full bg-red-500/80"></div>
                        <div class="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                        <div class="w-3 h-3 rounded-full bg-green-500/80"></div>
                    </div>
                    <span class="term-font text-[10px] text-zinc-500">root@vps-evolution:~# tail -f sniper.log</span>
                </div>
                <textarea id="caixa-log" class="w-full flex-1 bg-transparent p-5 term-font text-xs text-green-400/90 resize-none focus:outline-none leading-loose" readonly></textarea>
            </div>

            <!-- Controles Táticos -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button onclick="conectarApi()" class="bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-3">
                    <i class="fa-solid fa-qrcode text-zinc-400"></i> QR CODE
                </button>
                <button onclick="iniciar()" class="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-4 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all transform hover:-translate-y-1 flex items-center justify-center gap-3">
                    <i class="fa-solid fa-bolt"></i> ENGATILHAR MOTOR
                </button>
                <button onclick="abortar()" class="bg-red-950 hover:bg-red-900 border border-red-900/50 text-red-400 font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-3">
                    <i class="fa-solid fa-ban"></i> SUSPENDER
                </button>
            </div>
        </main>

        <script>
            // Carregar cofre no início
            window.onload = async () => {
                const res = await fetch('/api/config');
                const conf = await res.json();
                document.getElementById('shopee_id').value = conf.shopee_id;
                document.getElementById('shopee_secret').value = conf.shopee_secret;
                document.getElementById('nicho').value = conf.nicho;
                document.getElementById('grupos').value = conf.grupos;
                document.getElementById('tempo').value = conf.tempo;
                document.getElementById('aleatorio').checked = conf.aleatorio;
            };

            async function salvarConfig() {
                const btn = document.getElementById('btn-salvar');
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';
                
                const dados = {
                    shopee_id: document.getElementById('shopee_id').value,
                    shopee_secret: document.getElementById('shopee_secret').value,
                    nicho: document.getElementById('nicho').value,
                    grupos: document.getElementById('grupos').value,
                    tempo: parseInt(document.getElementById('tempo').value),
                    aleatorio: document.getElementById('aleatorio').checked
                };
                
                await fetch('/api/config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(dados) });
                
                setTimeout(() => { btn.innerHTML = '<i class="fa-solid fa-check text-green-400"></i> Salvo com Sucesso'; }, 500);
                setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-floppy-disk"></i> Salvar Cofre'; }, 2500);
            }

            async function conectarApi() { 
                document.getElementById('qr-container').classList.remove('hidden');
                document.getElementById('qr-container').classList.add('flex');
                document.getElementById('qr-img').src = "";
                await fetch('/api/conectar', { method: 'POST' }); 
                
                let tentativas = 0;
                let qrInterval = setInterval(async () => {
                    tentativas++;
                    const res = await fetch('/api/qrcode');
                    if(res.headers.get('content-type') && res.headers.get('content-type').includes('image')) {
                        document.getElementById('qr-img').src = '/api/qrcode?' + new Date().getTime();
                        clearInterval(qrInterval);
                    }
                    if(tentativas > 30) clearInterval(qrInterval);
                }, 2000);
            }
            
            async function iniciar() {
                await salvarConfig(); // Salva antes de rodar
                await fetch('/api/iniciar', { method: 'POST' }); 
            }
            async function abortar() { await fetch('/api/abortar', { method: 'POST' }); }

            // Lógica do Motor e Cronômetro em Tempo Real
            setInterval(async () => {
                try {
                    const res = await fetch('/api/status');
                    const dados = await res.json();
                    
                    document.getElementById('lbl-disparos').innerText = dados.disparos;
                    
                    // Ação Dinâmica
                    const lblAcao = document.getElementById('lbl-acao');
                    lblAcao.innerText = dados.acao;
                    if(dados.acao.includes("DIGITANDO")) {
                        lblAcao.className = "text-xl font-bold text-fuchsia-400 drop-shadow-[0_0_8px_rgba(232,121,249,0.8)] animate-pulse";
                    } else if (dados.acao === "INATIVO" || dados.acao.includes("PARANDO")) {
                        lblAcao.className = "text-xl font-bold text-zinc-500";
                    } else {
                        lblAcao.className = "text-xl font-bold text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]";
                    }
                    
                    // Relógio
                    const c = dados.cronometro;
                    const m = Math.floor(c / 60).toString().padStart(2, '0');
                    const s = (c % 60).toString().padStart(2, '0');
                    document.getElementById('lbl-cronometro').innerText = `${m}:${s}`;
                    
                    // Terminal Auto-Scroll
                    const logBox = document.getElementById('caixa-log');
                    if(logBox.value !== dados.logs) {
                        logBox.value = dados.logs;
                        logBox.scrollTop = logBox.scrollHeight;
                    }
                } catch (e) {}
            }, 1000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
