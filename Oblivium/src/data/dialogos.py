# data/dialogos.py

conversa_mundo = [
    {"autor": "Carroceiro", "texto": "Bem, na época de inverno é realmente cinzento, mas estamos em pleno verão, a grama é verde e o sol brilha, não entendi o que quis dizer."},
    {"autor": "Pensamento", "texto": "O mundo só é assim pra mim?..."},
]

conversa_critica = [
    {"autor": "Carroceiro", "texto": "Me perdoe... É que a senhorita mora bem longe (Ele claramente fica deprimido)."},
    {"autor": "Pensamento", "texto": "Por que eu falei isso?"},
]

conversa_outra_coisa = [
    {"autor": "Carroceiro", "texto": "A senhorita é a elfa que salvou o mundo do tirano rei demônio, os anciões da vila devem saber mais, aprendi apenas um pouco em minhas viagens."},
    {"autor": "Pensamento", "texto": "Eu salvei o mundo?... Tenho muitas perguntas a fazer."},
]

conversa_prosseguir = [
    {"autor": "Carroceiro", "texto": "Aperte os cintos. Suba na carroça, o caminho até a capital é longo e parece que vai neblinar."},
    {"autor": "Sistema", "texto": "Iniciando viagem rumo à capital..."}
]

# --- RESPOSTAS BOBAS PARA TESTAR PAGINAÇÃO ---
resposta_clima = [{"autor": "Carroceiro", "texto": "Pelo menos não está chovendo. Um tempo nublado é melhor para viajar."}]
resposta_lanche = [{"autor": "Carroceiro", "texto": "Tenho apenas pão duro e uma maçã pela metade. Aceita?"}]
resposta_estradas = [{"autor": "Carroceiro", "texto": "Desde a queda do tirano, monstros menores andam famintos pela região."}]
resposta_animal = [{"autor": "Carroceiro", "texto": "Sempre fui muito apegado aos cavalos. O meu se chama Trovão."}]
resposta_cantar = [{"autor": "Carroceiro", "texto": "Só depois de beber muito hidromel na taverna da capital!"}]

no_escolhas_carroceiro = {
    "pode_fechar": True,  # Habilita o botão [X] especificamente para este menu
    "resultado_fechar": [{"autor": "Carroceiro", "texto": "Tudo bem, estarei aguardando aqui. Me avise quando estiver pronta."}],
    "escolhas": [
        {"id": "sobre_mundo", "texto": "O mundo sempre foi tão cinza assim?", "resultado": conversa_mundo},
        {"id": "criticar_demora", "texto": "Pensei que você sabia se orientar", "resultado": conversa_critica},
        {"id": "sobre_passado", "texto": "Falar sobre outra coisa (Meu passado)", "resultado": conversa_outra_coisa},
        
        # --- OPÇÕES EXTRAS PARA FORÇAR PAGINAÇÃO ---
        {"id": "teste_1", "texto": "Sobre o clima de hoje...", "resultado": resposta_clima},
        {"id": "teste_2", "texto": "Você tem um lanche na carroça?", "resultado": resposta_lanche},
        {"id": "teste_3", "texto": "Por que as estradas estão tão perigosas?", "resultado": resposta_estradas},
        {"id": "teste_4", "texto": "Qual o seu animal favorito?", "resultado": resposta_animal},
        {"id": "teste_5", "texto": "Você gosta de cantar?", "resultado": resposta_cantar},
        
        {"id": "prosseguir", "texto": "Deseja prosseguir viagem", "resultado": conversa_prosseguir} 
    ]
}

conversa_mundo.append(no_escolhas_carroceiro)
conversa_critica.append(no_escolhas_carroceiro)
conversa_outra_coisa.append(no_escolhas_carroceiro)
resposta_clima.append(no_escolhas_carroceiro)
resposta_lanche.append(no_escolhas_carroceiro)
resposta_estradas.append(no_escolhas_carroceiro)
resposta_animal.append(no_escolhas_carroceiro)
resposta_cantar.append(no_escolhas_carroceiro)

dialogo_hub_carroceiro = [
    {"autor": "Carroceiro", "texto": "Ah, finalmente nos encontramos, demorei um pouco para achar sua casa."},
    no_escolhas_carroceiro
]

conversa_pos_fogo = [
    {"autor": "Carroceiro", "texto": "Pelos deuses, que explosão foi essa? Meus ouvidos ainda estão zumbindo!"},
    {"autor": "Halia", "texto": "O caminho está livre. Podemos prosseguir."},
    {"autor": "Carroceiro", "texto": "Sim, vamos rápido... Espera. Você ouviu isso? O estrondo atraiu algo!"},
    {"autor": "Narrador", "texto": "Das sombras da estrada, duas criaturas rastejam na sua direção!"},
    {"autor": "Sistema", "texto": "PREPARE-SE PARA O COMBATE! (2 Inimigos)"}
]

conversa_pos_levitar = [
    {"autor": "Carroceiro", "texto": "Você moveu toneladas de rocha como se fossem folhas secas... Incrível."},
    {"autor": "Halia", "texto": "O caminho está livre. Podemos prosseguir."},
    {"autor": "Carroceiro", "texto": "Vamos antes que a neblina... shhh. Algo muito grande está vindo."},
    {"autor": "Narrador", "texto": "A forte concentração de mana atraiu uma anomalia poderosa..."},
    {"autor": "Sistema", "texto": "PREPARE-SE PARA O COMBATE! (1 Inimigo Forte)"}
]

textos_flashback_magia = [
    {"autor": "Narrador", "texto": "Ao tocar na pedra fria, o som do vento ao teu redor desaparece..."},
    {"autor": "Eco do Passado", "texto": "Halia... Lembra-te do teu nome. Lembra-te de quem eras antes do silêncio cinzento."},
    {"autor": "Pensamento", "texto": "A minha mente... Está a arder. Eu consigo ver fardos de luz e calor nas minhas mãos... Eu sei usar magia!"},
    {"autor": "Sistema", "texto": "A tua ligação com a mana ancestral foi reestabelecida."}
]

conversa_tentar_fogo = [
    {"autor": "Pensamento", "texto": "Se eu me concentrar, talvez consiga conjurar uma explosão para estilhaçar estas rochas!"},
    {"autor": "Sistema", "texto": "Magia de Fogo selecionada. Prepare-se para mirar!"}
]

conversa_tentar_levitacao = [
    {"autor": "Pensamento", "texto": "Se eu canalizar a energia ao redor das fendas, posso fazer estas pedras flutuarem para fora da estrada."},
    {"autor": "Sistema", "texto": "Magia de Levitação selecionada. Prepare-se para concentrar a mana!"}
]

no_escolhas_magias = {
    "pode_fechar": True,
    "id_cancelamento": "voltar_magia", 
    "escolhas": [
        {"id": "escolha_fogo", "texto": "Conjurar Magia de Fogo (Puzzle de Mira)", "resultado": conversa_tentar_fogo, "repetivel": True},
        {"id": "escolha_levitar", "texto": "Conjurar Magia de Levitação (Puzzle de Concentração)", "resultado": conversa_tentar_levitacao, "repetivel": True}
    ]
}

no_escolha_inicial_puzzle = {
    "pode_fechar": True,
    "id_cancelamento": "desistir_puzzle", 
    "escolhas": [
        {"id": "analisar_pedras", "texto": "Analisar as pedras caídas detalhadamente", "resultado": []}
    ]
}

dialogo_investigar_pedras = [
    {"autor": "Halia", "texto": "Estas pedras são enormes... Força física não vai resolver isto."},
    no_escolha_inicial_puzzle
]

# --- Diálogos de Feedback de Minijogos ---
dialogo_falha_timing = [
    {"autor": "Halia", "texto": "A magia dissipou-se nas minhas mãos... Perdi o tempo certo. Preciso focar-me e tentar novamente."},
    no_escolhas_magias 
]

dialogo_falha_mash = [
    {"autor": "Halia", "texto": "As pedras ficaram pesadas demais... Perdi a concentração. Preciso tentar novamente."},
    no_escolhas_magias
]

# --- Triggers do Overworld ---
dialogo_fechar_porta = [
    {"autor": "Pensamento", "texto": "Quem sai de casa sem fechar a porta? Não posso deixar tudo aberto..."},
    {"autor": "Sistema", "texto": "Você fechou a porta de casa de forma segura."}
]

dialogo_avistar_carroceiro = [
    {"autor": "Pensamento", "texto": "Tem alguém vindo com uma carroça... É ele!"}
]

dialogo_porta_abriu = [
    {"autor": "Halia", "texto": "Pronto, estou com tudo. A porta destrancou."},
    {"autor": "Sistema", "texto": "A porta está aberta. Use o direcional para sair para a varanda."}
]

dialogo_porta_trancada = [
    {"autor": "Pensamento", "texto": "Ainda não peguei tudo o que preciso. Não posso sair de mãos vazias."}
]

# --- Diálogos de Entrada de Áreas (Cutscenes de Transição) ---
dialogo_entrada_estrada1 = [
    {"autor": "Halia", "texto": "Que vento frio... O mundo continua completamente cinzento e sem vida por aqui fora."},
    {"autor": "Pensamento", "texto": "Onde estará aquele homem com a carroça? Ele disse que me esperaria ao longo desta estrada de terra."},
    {"autor": "Sistema", "texto": "Objetivo: Siga para a direita ao longo da estrada para procurar o carroceiro."}
]

dialogo_entrada_estrada2 = [
    {"autor": "Narrador", "texto": "Algumas horas de viagem depois... A carroça para abruptamente."},
    {"autor": "Carroceiro", "texto": "Pelos deuses... Um deslizamento de terra! Olhe o tamanho daquelas pedras bloqueando o caminho."},
    {"autor": "Pensamento", "texto": "Preciso dar uma olhada de perto nessas pedras para ver se encontro uma solução."}
]

# --- Interações Específicas do Carroceiro na Estrada_2 ---
dialogo_carroceiro_pos_puzzle = [
    {"autor": "Carroceiro", "texto": "Cuidado com essas criaturas, Halia!"}
]

dialogo_carroceiro_impedimento = [
    {"autor": "Carroceiro", "texto": "Não há como passar com a carroça por aqui. Precisamos de dar um jeito nestas pedras!"}
]