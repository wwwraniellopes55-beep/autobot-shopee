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
from playwright.sync_api import sync_playwright

app = FastAPI(title="Shopee AutoBot SaaS")

# ==========================================
# CREDENCIAIS E ESTADO
# ==========================================
SHOPEE_APP_ID = "18380880065"
SHOPEE_SECRET = "42LRGW5UMGFZOF65ZKZOYIV6T7VJ7DX7"

estado_robo = {
    "ligado": False,
    "disparos": 0,
    "protecoes": 0,
    "inicio_sessao": 0,
    "logs": ["Sistema Inicializado.", "> Motor FastAPI na Nuvem Operacional."]
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
# MOTORES PLAYWRIGHT (AGORA INVISÍVEIS)
# ==========================================
def motor_conectar():
    if os.path.exists("qrcode.png"):
        os.remove("qrcode.png")
        
    try:
        add_log("Iniciando navegador fantasma na nuvem com camuflagem...")
        with sync_playwright() as p:
            caminho_perfil = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessao_whatsapp")
            navegador = p.chromium.launch_persistent_context(
                user_data_dir=caminho_perfil, 
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                args=[
                    "--no-sandbox", 
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled", 
                    "--disable-infobars"
                ]
            )
            pagina = navegador.pages[0] if navegador.pages else navegador.new_page()
            pagina.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            pagina.goto("https://web.whatsapp.com/")
            
            add_log("Aguardando sistema do WhatsApp...")
            try:
                pagina.wait_for_selector('canvas', timeout=60000)
                add_log("Gerando imagem do QR Code para o painel...")
                pagina.locator('canvas').screenshot(path="qrcode.png")
                add_log("⚠️ QR Code gerado! Escaneie a imagem que apareceu na tela.")
                
                pagina.wait_for_selector('#pane-side', timeout=45000)
                add_log("✅ Conexão autorizada e salva com sucesso!")
                if os.path.exists("qrcode.png"): os.remove("qrcode.png")
            except:
                if pagina.locator('#pane-side').is_visible():
                    add_log("✅ O WhatsApp já estava conectado!")
                else:
                    add_log("Tempo esgotado ou erro ao ler. Tente conectar novamente.")
            
            time.sleep(2)
            navegador.close()
            add_log("Sessão de configuração encerrada.")
    except Exception as e:
        add_log(f"Erro na conexão: {str(e)}")

def motor_iniciar_disparos(nicho, aleatorio, grupos_str, tempo_base):
    lista_grupos = [g.strip() for g in grupos_str.split(',') if g.strip()]
    if not lista_grupos:
        add_log("ERRO: Nenhum grupo informado!")
        estado_robo["ligado"] = False
        return

    nichos_em_alta = ["Fone Sem Fio", "Smartwatch", "Tênis Masculino", "Moda Feminina"]

    try:
        add_log("Inicializando motor de disparos invisível com camuflagem...")
        with sync_playwright() as p:
            caminho_perfil = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessao_whatsapp")
            navegador = p.chromium.launch_persistent_context(
                user_data_dir=caminho_perfil, 
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                args=[
                    "--no-sandbox", 
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled", 
                    "--disable-infobars"
                ]
            )
            pagina = navegador.pages[0] if navegador.pages else navegador.new_page()
            pagina.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            pagina.goto("https://web.whatsapp.com/")
            
            pagina.wait_for_selector('#pane-side', timeout=60000) 
            add_log("WhatsApp validado. Iniciando varredura de ofertas...")
            
            while estado_robo["ligado"]:
                nicho_atual = random.choice(nichos_em_alta) if aleatorio else nicho
                add_log(f"Buscando produto na Shopee (Nicho: {nicho_atual})...")
                produto = puxar_shopee(f"{nicho_atual} mais vendidos")
                copy = criar_copy(produto)

                caminho_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "produto_temp.jpg")
                if produto.get("imagem_url"):
                    open(caminho_img, 'wb').write(requests.get(produto["imagem_url"]).content)

                for nome_grupo in lista_grupos:
                    if not estado_robo["ligado"]: break
                    
                    add_log(f"Acessando grupo: {nome_grupo}...")
                    pagina.keyboard.press("Control+Alt+/")
                    time.sleep(1.5)
                    pagina.keyboard.insert_text(nome_grupo)
                    time.sleep(2.5)
                    pagina.keyboard.press("Enter")
                    time.sleep(4) 
                    
                    if os.path.exists(caminho_img):
                        try:
                            pagina.locator('div[title="Anexar"], div[title="Attach"], span[data-icon="plus"]').first.click(timeout=5000)
                        except:
                            pagina.locator('span[data-icon="clip"]').first.click(timeout=5000)
                        
                        time.sleep(1.5)
                        pagina.locator('input[type="file"]').first.set_input_files(caminho_img)
                        time.sleep(3) 
                        pagina.keyboard.insert_text(copy)
                        time.sleep(1)
                        pagina.keyboard.press("Enter")
                    else:
                        pagina.keyboard.insert_text(copy)
                        time.sleep(1)
                        pagina.keyboard.press("Enter")
                    
                    estado_robo["disparos"] += 1
                    add_log(f"Oferta disparada com sucesso em: {nome_grupo}")
                    time.sleep(random.uniform(2.5, 4.5)) 
                
                if os.path.exists(caminho_img): os.remove(caminho_img)
                
                add_log(f"Ciclo concluído. Pausa antiban de {tempo_base}s...")
                for i in range(tempo_base):
                    if not estado_robo["ligado"]: break
                    time.sleep(1)
                    
            navegador.close()
            add_log("Operação abortada. Motor desligado.")
    except Exception as e:
        add_log(f"ERRO CRÍTICO: {str(e)}")
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
    if not estado_robo["ligado"]:
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
# FRONTEND RESPONSIVO
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
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
            body { 
                background-color: #0f172a;
                background-image: radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.4) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.4) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(239, 68, 68, 0.2) 0px, transparent 50%);
                background-attachment: fixed; color: #e2e8f0; font-family: 'Outfit', sans-serif;
            }
            .glass { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5); }
            .input-dark { background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; color: #fff; padding: 10px 12px; width: 100%; outline: none; transition: 0.3s; font-size: 0.9rem; }
            .input-dark:focus { border-color: #3b82f6; box-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }
            .terminal { background: rgba(0, 0, 0, 0.65); color: #34d399; font-family: 'Consolas', monospace; border: 1px solid rgba(255, 255, 255, 0.05); min-height: 200px; }
            ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 10px; }
        </style>
    </head>
    <body class="flex flex-col md:flex-row min-h-screen overflow-y-auto overflow-x-hidden">
        
        <aside class="w-full md:w-80 glass p-6 flex flex-col gap-6 relative z-10 border-b md:border-b-0 md:border-r border-gray-700/50">
            <div class="text-center mb-2 mt-2">
                <h1 class="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-rose-500">
                    <i class="fa-solid fa-robot mr-2 text-orange-500"></i>AutoBot PRO
                </h1>
            </div>
            
            <div class="space-y-5">
                <div>
                    <label class="block text-xs font-bold mb-2 text-gray-400 uppercase tracking-wider">Nicho</label>
                    <input type="text" id="inp-nicho" value="Eletrônicos" class="input-dark">
                    <label class="flex items-center gap-2 mt-2 cursor-pointer text-sm text-gray-300 hover:text-white">
                        <input type="checkbox" id="chk-aleatorio" class="accent-orange-500 w-4 h-4 rounded"> Modo Aleatório (Em Alta)
                    </label>
                </div>
                <div>
                    <label class="block text-xs font-bold mb-2 text-gray-400 uppercase tracking-wider">Multi-Grupos</label>
                    <input type="text" id="inp-grupos" placeholder="Ex: Grupo 1, Grupo 2" class="input-dark">
                </div>
                <div>
                    <label class="block text-xs font-bold mb-2 text-gray-400 uppercase tracking-wider">Intervalo (Segundos)</label>
                    <input type="number" id="inp-tempo" value="15" class="input-dark">
                </div>
            </div>
        </aside>

        <main class="flex-1 p-4 md:p-8 flex flex-col gap-5 relative z-10 w-full">
            
            <!-- CAIXA DO QR CODE OCULTA -->
            <div id="qr-container" class="hidden flex-col items-center justify-center p-6 glass rounded-xl border border-yellow-500/30">
                <p class="text-yellow-400 font-bold mb-4 text-center"><i class="fa-solid fa-qrcode mr-2"></i>Escaneie o QR Code para conectar</p>
                <div class="bg-white p-2 rounded-lg">
                    <img id="qr-img" src="" class="w-48 h-48 md:w-64 md:h-64 object-contain">
                </div>
                <p class="text-xs text-gray-400 mt-4 text-center">Aguarde a imagem aparecer. Pode levar até 15 segundos.</p>
            </div>

            <div class="glass rounded-xl p-4 flex flex-col md:flex-row justify-between items-center border-l-4 border-l-blue-500 gap-4 md:gap-0 mt-2">
                <div class="flex items-center gap-4 w-full md:w-1/4">
                    <div id="status-bg" class="w-12 h-12 rounded-lg bg-gray-700/50 flex items-center justify-center shrink-0">
                        <i id="status-icon" class="fa-solid fa-power-off text-xl text-gray-400"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 uppercase font-bold tracking-widest">Motor Web</p>
                        <p id="status-texto" class="text-lg font-extrabold text-gray-300">STANDBY</p>
                    </div>
                </div>
                <div class="w-full h-px md:w-px md:h-10 bg-white/10 my-2 md:my-0"></div>
                <div class="flex items-center gap-4 w-full md:w-1/4 md:justify-center">
                    <div class="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center shrink-0">
                        <i class="fa-solid fa-paper-plane text-xl text-green-400"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400 uppercase font-bold tracking-widest">Disparos</p>
                        <p id="lbl-disparos" class="text-2xl font-extrabold text-white">0</p>
                    </div>
                </div>
                <div class="w-full h-px md:w-px md:h-10 bg-white/10 my-2 md:my-0"></div>
                <div class="flex items-center gap-4 w-full md:w-1/4 md:justify-end">
                    <div class="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center shrink-0">
                        <i class="fa-solid fa-clock text-xl text-purple-400"></i>
                    </div>
                    <div class="md:text-right">
                        <p class="text-xs text-gray-400 uppercase font-bold tracking-widest">Uptime</p>
                        <p id="lbl-tempo" class="text-2xl font-extrabold text-white tracking-tight">00:00:00</p>
                    </div>
                </div>
            </div>

            <div class="flex-1 flex flex-col mt-2 glass rounded-xl p-1 min-h-[250px]">
                <div class="flex items-center gap-2 px-4 py-2 border-b border-white/5 bg-black/40 rounded-t-xl">
                    <div class="w-3 h-3 rounded-full bg-red-500"></div><div class="w-3 h-3 rounded-full bg-yellow-500"></div><div class="w-3 h-3 rounded-full bg-green-500"></div>
                    <span class="ml-2 text-xs text-gray-500 font-mono"><i class="fa-solid fa-terminal mr-2"></i>console_output</span>
                </div>
                <textarea id="caixa-log" class="terminal w-full flex-1 p-5 resize-none text-sm focus:outline-none rounded-b-xl" readonly></textarea>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mt-2">
                <button onclick="conectarApi()" class="bg-blue-600/90 hover:bg-blue-500 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] flex items-center justify-center gap-3">
                    <i class="fa-solid fa-mobile-screen"></i> CONECTAR WPP
                </button>
                <button onclick="iniciarDisparos()" class="bg-emerald-600/90 hover:bg-emerald-500 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_15px_rgba(5,150,105,0.4)] flex items-center justify-center gap-3">
                    <i class="fa-solid fa-play"></i> INICIAR MOTOR
                </button>
                <button onclick="abortarTudo()" class="bg-rose-600/90 hover:bg-rose-500 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_15px_rgba(225,29,72,0.4)] flex items-center justify-center gap-3">
                    <i class="fa-solid fa-stop"></i> ABORTAR
                </button>
            </div>
        </main>

        <script>
            async function conectarApi() { 
                document.getElementById('qr-container').classList.remove('hidden');
                document.getElementById('qr-img').src = "";
                await fetch('/api/conectar', { method: 'POST' }); 
                
                // Sistema de busca automática do QR Code
                let tentativas = 0;
                let qrInterval = setInterval(async () => {
                    tentativas++;
                    const res = await fetch('/api/qrcode');
                    if(res.headers.get('content-type') && res.headers.get('content-type').includes('image')) {
                        document.getElementById('qr-img').src = '/api/qrcode?' + new Date().getTime();
                        clearInterval(qrInterval);
                        setTimeout(() => { document.getElementById('qr-container').classList.add('hidden'); }, 30000); // Esconde após 30s
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
                        bg.className = "w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center shrink-0 animate-pulse";
                        icon.className = "fa-solid fa-satellite-dish text-xl text-green-400";
                        txt.className = "text-lg font-extrabold text-green-400";
                        txt.innerText = "ONLINE";
                    } else {
                        bg.className = "w-12 h-12 rounded-lg bg-gray-700/50 flex items-center justify-center shrink-0";
                        icon.className = "fa-solid fa-power-off text-xl text-gray-400";
                        txt.className = "text-lg font-extrabold text-gray-300";
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