# ETAPA 1: PESQUISA FORÇADA POR TECLADO
                    try:
                        # 1. Usa o atalho nativo do WhatsApp para focar na pesquisa (não falha)
                        pagina.keyboard.press("Control+Alt+/")
                        time.sleep(1.5)
                        
                        # 2. Seleciona tudo e apaga (limpa textos de buscas anteriores)
                        pagina.keyboard.press("Control+A")
                        pagina.keyboard.press("Backspace")
                        
                        # 3. Digita o nome do grupo exato
                        pagina.keyboard.insert_text(nome_grupo)
                        
                        # 4. Tempo absoluto de espera para a lista do WhatsApp filtrar os contatos
                        time.sleep(3.5) 
                        
                        # 5. MODO TECLADO: Desce para o primeiro resultado da lista e entra
                        pagina.keyboard.press("ArrowDown")
                        time.sleep(0.5)
                        pagina.keyboard.press("Enter")
                        time.sleep(2)
                            
                        # 6. VALIDAÇÃO VERDADEIRA: Lê o nome do chat aberto no topo direito
                        if not pagina.locator('header').filter(has_text=nome_grupo).is_visible(timeout=5000):
                            add_log(f"Erro: Não foi possível abrir o grupo '{nome_grupo}'.")
                            continue
                            
                    except Exception as e:
                        add_log(f"Erro de interface ao buscar o grupo '{nome_grupo}'.")
                        continue
