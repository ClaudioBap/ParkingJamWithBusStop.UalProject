# ficheiro: Projeto/jogo.py

from autocarro import Autocarro
from tabuleiro import Tabuleiro
from passageiro import Passageiro
import random
import math

class Jogo:
    # Grelha 12x12 padrão (o estado "perfeito" que tinhas)
    def __init__(self, largura=12, altura=12):
        """Inicializador da lógica principal do jogo (com geração aleatória)."""
        self.tabuleiro = Tabuleiro(largura, altura)
        self.movimentos = 0
        self.passageiros = [] # Lista total de todos os passageiros gerados
        self.cores_jogo = ["blue", "green", "yellow", "orange", "purple", "red", "cyan", "magenta"]
        self.capacidades_validas = [2, 4, 6, 8, 12]
        self.cores_ativas = []
        # NOVO: Fila aleatória de passageiros (inicializada vazia)
        # Esta fila representará o estado INICIAL e não será alterada pelo embarque
        self.fila_aleatoria = []

        # NOVO: Dicionário para armazenar autocarros estacionados por cor ativa
        # Inicializa com listas vazias para cada cor ativa (serão definidas em gerar_configuracao_inicial)
        self.estacionamento_por_cor = {}

        # --- CHAMA A GERAÇÃO ALEATÓRIA ---
        self.gerar_configuracao_inicial_wrapper() # <-- USA A GERAÇÃO ALEATÓRIA
        # ---------------------------------

        # Garante que o dicionário de estacionamento é inicializado com as cores ativas geradas
        self.estacionamento_por_cor = {color: [] for color in self.cores_ativas}


    def gerar_configuracao_inicial_wrapper(self):
        """Tenta gerar a configuração inicial várias vezes se necessário."""
        success = False; max_gen_attempts = 10
        for attempt in range(max_gen_attempts):
            print(f"\n--- Tentativa de Geração {attempt + 1}/{max_gen_attempts} ---")
            # Chama a função que gera aleatoriamente
            success = self.gerar_configuracao_inicial()
            if success:
                print("--- Geração bem-sucedida! ---")
                # NOVO: Criar a fila aleatória SOMENTE após uma geração bem-sucedida
                # E esta fila NÃO SERÁ ALTERADA PELO EMBARQUE
                print("DEBUG: A criar fila aleatória (estática) após a geração inicial bem-sucedida.")
                # A fila aleatória é criada aqui com base nos passageiros iniciais e mantém-se estática
                self.fila_aleatoria = self.criar_fila_aleatoria()
                print(f"DEBUG: Fila aleatória (estática) criada com {len(self.fila_aleatoria)} passageiros.")

                # NOVO: Inicializar o dicionário de estacionamento com as cores ativas geradas
                self.estacionamento_por_cor = {color: [] for color in self.cores_ativas}
                print(f"DEBUG: Dicionário de estacionamento inicializado para as cores: {list(self.estacionamento_por_cor.keys())}")


                break # Sai do loop de tentativas se for bem-sucedido
            else:
                print("--- Geração falhou (posicionamento), a tentar novamente... ---")
                # Limpar listas em caso de falha para tentar novamente
                self.tabuleiro.autocarros = []
                self.passageiros = []
                self.cores_ativas = []
                self.fila_aleatoria = [] # Garantir que a fila fica vazia após falha
                self.estacionamento_por_cor = {} # Limpar dicionário de estacionamento


        if not success:
            print("ERRO FATAL: Não foi possível gerar uma configuração inicial válida.")
            # Garantir que as listas ficam vazias se a geração falhar completamente
            self.tabuleiro.autocarros = []
            self.passageiros = []
            self.cores_ativas = []
            self.fila_aleatoria = []
            self.estacionamento_por_cor = {}


    def gerar_configuracao_inicial(self) -> bool:
        """Gera passageiros e autocarros aleatoriamente."""
        # --- 0. Reset ---
        self.tabuleiro.autocarros = []; self.passageiros = []; self.cores_ativas = []
        posicoes_ocupadas_geral = set()
        # self.estacionamento_por_cor será inicializado no wrapper após a geração das cores ativas


        # --- 1. Definir Cores/Passageiros Aleatoriamente ---
        num_cores_nivel = random.randint(4, 8) # 4 a 8 cores
        if len(self.cores_jogo) < num_cores_nivel: num_cores_nivel = len(self.cores_jogo)
        self.cores_ativas = random.sample(self.cores_jogo, num_cores_nivel)
        print(f"Cores ativas ({len(self.cores_ativas)}): {self.cores_ativas}")
        passageiros_por_cor = {cor: random.randint(5, 15) for cor in self.cores_ativas}
        print(f"Passageiros necessários: {passageiros_por_cor}")
        id_pass = 0
        for cor, count in passageiros_por_cor.items():
            for _ in range(count):
                # Adiciona passageiros à lista total de passageiros
                self.passageiros.append(Passageiro(id_pass, -1, -1, cor))
                id_pass += 1
        print(f"Total de {len(self.passageiros)} passageiros criados.")

        # NOVO DEBUG: Verificar quantos passageiros estão 'esperando' após a criação
        passageiros_esperando_count = sum(1 for p in self.passageiros if p.estado == 'esperando')
        print(f"DEBUG: {passageiros_esperando_count} passageiros no estado 'esperando' após a criação.")


        # --- 2. Gerar Autocarros Necessários Aleatoriamente ---
        autocarros_necessarios = []; print("Gerando autocarros necessários...")
        for cor in self.cores_ativas:
            total_pax = passageiros_por_cor[cor]; capacidade_total_gerada_cor = 0; autocarros_desta_cor = []
            while capacidade_total_gerada_cor < total_pax or not autocarros_desta_cor:
                # Usa capacidades válidas para autocarros de cor ativa
                capacidade = random.choice(self.capacidades_validas) # Usa [2, 4, 6, 8, 12]
                direcao = random.choice(["H", "V"])
                novo_bus = Autocarro(0, 0, direcao, capacidade, cor)
                autocarros_desta_cor.append(novo_bus); capacidade_total_gerada_cor += capacidade
            autocarros_necessarios.extend(autocarros_desta_cor)

        # --- 3. Posicionar Autocarros Necessários (ALEATÓRIO com 200 Tentativas) ---
        print(f"A tentar posicionar {len(autocarros_necessarios)} autocarros necessários (Random)...")
        random.shuffle(autocarros_necessarios)
        for bus in autocarros_necessarios:
            posicionado = False
            max_pos_attempts = 200 # <-- Número original de tentativas aleatórias
            for _ in range(max_pos_attempts):
                # Garante que o autocarro cabe na grelha principal 12x12 (self.tabuleiro)
                max_x = self.tabuleiro.largura - (bus.capacidade if bus.direcao == "H" else 1)
                max_y = self.tabuleiro.altura - (1 if bus.direcao == "H" else bus.capacidade)
                if max_x < 0 or max_y < 0: continue # Se a capacidade for maior que a dimensão, pula
                temp_x = random.randint(0, max_x); temp_y = random.randint(0, max_y)
                bus.x = temp_x; bus.y = temp_y
                posicoes_tentativa = set(bus.obter_posicoes_ocupadas())
                if posicoes_tentativa.isdisjoint(posicoes_ocupadas_geral):
                    self.tabuleiro.adicionar_autocarro(bus)
                    posicoes_ocupadas_geral.update(posicoes_tentativa)
                    posicionado = True; break
            if not posicionado:
                print(f"ERRO GERAÇÃO: Posicionamento aleatório falhou para o autocarro {bus} após {max_pos_attempts} tentativas.")
                # Se um autocarro necessário não puder ser posicionado, a geração falha.
                return False

        # --- 4. Adicionar Bloqueadores Aleatoriamente ---
        # Estes são autocarros adicionais que não correspondem a cores de passageiros.
        num_bloqueadores = random.randint(6, 12) # Número original de bloqueadores
        print(f"A tentar adicionar {num_bloqueadores} bloqueadores...")
        # Usar cores que não estão ativas para os passageiros, mais algumas cores neutras.
        cores_bloqueio_disponiveis = [cor for cor in self.cores_jogo if cor not in self.cores_ativas] + ["gray", "brown", "black"]
        bloqueadores_adicionados = 0
        for _ in range(num_bloqueadores):
            posicionado_block = False; max_block_attempts = 100
            for _ in range(max_block_attempts):
                 # Capacidade [2, 4] para bloqueadores (geralmente mais curtos)
                 capacidade = random.choice([2, 4])
                 direcao = random.choice(["H", "V"])
                 # Escolher uma cor de bloqueio disponível
                 if not cores_bloqueio_disponiveis: # Se não houver cores de bloqueio disponíveis, usar cores ativas (menos ideal)
                      cor = random.choice(self.cores_jogo)
                 else:
                    cor = random.choice(cores_bloqueio_disponiveis)

                 # Garante que o bloqueador cabe na grelha principal
                 max_x = self.tabuleiro.largura - (capacidade if direcao == "H" else 1)
                 max_y = self.tabuleiro.altura - (1 if direcao == "H" else capacidade)
                 if max_x < 0 or max_y < 0: continue # Se a capacidade for maior que a dimensão, pula
                 temp_x = random.randint(0, max_x); temp_y = random.randint(0, max_y)
                 try:
                     bloqueador = Autocarro(temp_x, temp_y, direcao, capacidade, cor)
                     posicoes_tentativa = set(bloqueador.obter_posicoes_ocupadas())
                     if posicoes_tentativa.isdisjoint(posicoes_ocupadas_geral):
                         self.tabuleiro.adicionar_autocarro(bloqueador); posicoes_ocupadas_geral.update(posicoes_tentativa)
                         posicionado_block = True; bloqueadores_adicionados += 1; break
                 except ValueError as e:
                     # Continua se houver um erro na criação do autocarro (ex: capacidade inválida, embora validado)
                     continue
            # Não é crítico se falhar em adicionar todos os bloqueadores
            if not posicionado_block:
                print(f"Aviso: Falha ao posicionar um bloqueador após {max_block_attempts} tentativas.")


        print(f"Geração finalizada. Bloqueadores Adicionados: {bloqueadores_adicionados}/{num_bloqueadores}. Total autocarros no tabuleiro: {len(self.tabuleiro.autocarros)}")
        return True # Sucesso na geração dos autocarros necessários e posicionamento inicial

    # --- Métodos de Ajuda e Validação ---
    def obter_passageiros_por_cor(self, cor, estado="esperando"):
        """Retorna uma lista de passageiros de uma cor específica e num dado estado."""
        # Este método agora busca no total de passageiros (self.passageiros)
        return [p for p in self.passageiros if p.cor == cor and p.estado == estado]

    def is_move_valid(self, autocarro_a_mover: Autocarro, dx: int, dy: int) -> bool:
        """Verifica se um movimento de autocarro é válido (dentro dos limites e sem colisões)."""
        # Posição da cabeça do autocarro após o movimento
        nova_x_cabeca = autocarro_a_mover.x + dx
        nova_y_cabeca = autocarro_a_mover.y + dy
        novas_posicoes_ocupadas = set()

        # Calcular as novas posições que o autocarro ocuparia
        for i in range(autocarro_a_mover.capacidade):
            if autocarro_a_mover.direcao == "H":
                pos = (nova_x_cabeca + i, nova_y_cabeca)
            else: # Direção "V"
                pos = (nova_x_cabeca, nova_y_cabeca + i)

            # Verificar limites do tabuleiro principal
            if not (0 <= pos[0] < self.tabuleiro.largura and 0 <= pos[1] < self.tabuleiro.altura):
                # print(f"DEBUG is_move_valid: Fora dos limites em {pos}")
                return False
            novas_posicoes_ocupadas.add(pos)

        # Verificar colisões com outros autocarros
        posicoes_ocupadas_outros = set()
        for outro_autocarro in self.tabuleiro.autocarros:
            if outro_autocarro != autocarro_a_mover:
                posicoes_ocupadas_outros.update(outro_autocarro.obter_posicoes_ocupadas())

        if not novas_posicoes_ocupadas.isdisjoint(posicoes_ocupadas_outros):
            # print(f"DEBUG is_move_valid: Colisão detectada com outro autocarro.")
            return False # Colisão com outro autocarro

        # Se chegou aqui, o movimento é válido
        # print(f"DEBUG is_move_valid: Movimento válido para ({dx}, {dy}).")
        return True

    def find_suggestion(self):
        """
        Procura o primeiro autocarro que pode mover-se para a frente
        na sua direção e retorna esse autocarro e a direção do movimento.
        Retorna (None, 0, 0) se nenhuma sugestão for encontrada.
        """
        # Baralha a lista para dar uma "sugestão" diferente cada vez
        autocarros_shuffled = list(self.tabuleiro.autocarros)
        random.shuffle(autocarros_shuffled)

        for autocarro in autocarros_shuffled:
            # Tenta mover 1 unidade na sua direção
            dx, dy = 0, 0
            if autocarro.direcao == "H":
                dx = 1
            elif autocarro.direcao == "V":
                dy = 1

            # Verifica se este movimento é válido
            if self.is_move_valid(autocarro, dx, dy):
                # Verifica se não é uma tentativa de saída da grelha principal
                # A sugestão deve ser para mover DENTRO do tabuleiro, não para sair para a estação/embarque
                largura_tab = self.tabuleiro.largura
                altura_tab = self.tabuleiro.altura

                # Calcula a posição final da 'cauda' do autocarro após o movimento
                if autocarro.direcao == "H":
                    pos_final_cauda_x = autocarro.x + autocarro.capacidade -1 + dx
                    pos_final_cauda_y = autocarro.y + dy # Y não muda para H
                else: # Direção V
                    pos_final_cauda_x = autocarro.x + dx # X não muda para V
                    pos_final_cauda_y = autocarro.y + autocarro.capacidade - 1 + dy


                # Uma sugestão válida é um movimento *dentro* do tabuleiro
                # Portanto, a posição final da cauda deve estar dentro dos limites.
                if (0 <= pos_final_cauda_x < largura_tab) and (0 <= pos_final_cauda_y < altura_tab):
                     print(f"Sugestão encontrada: Mover {autocarro.cor} em ({dx}, {dy})")
                     return (autocarro, dx, dy) # Retorna o autocarro sugerido e o movimento
                else:
                     # Este movimento leva o autocarro para fora do tabuleiro principal.
                     # Não é uma sugestão de movimento *dentro* do tabuleiro.
                     # print(f"DEBUG Sugestão: Movimento de saída para {autocarro.cor} ignorado como sugestão.")
                     pass # Continua para o próximo autocarro

        print("Nenhuma sugestão de movimento encontrada no tabuleiro principal.")
        return (None, 0, 0) # Nenhuma sugestão encontrada

    # NOVO MÉTODO: Criar fila aleatória de passageiros
    def criar_fila_aleatoria(self):
        """Cria e retorna uma lista aleatória de todos os passageiros esperando.
           Esta lista é para representação visual estática do estado inicial."""
        # Pega todos os passageiros que foram criados inicialmente
        passageiros_iniciais_esperando = [p for p in self.passageiros if p.estado == 'esperando']
        print(f"DEBUG (criar_fila_aleatoria): Encontrados {len(passageiros_iniciais_esperando)} passageiros no estado 'esperando' inicialmente.")
        # Baralha a lista para torná-la aleatória
        random.shuffle(passageiros_iniciais_esperando)
        print(f"DEBUG (criar_fila_aleatoria): Criada fila aleatória (estática) com {len(passageiros_iniciais_esperando)} passageiros.")
        return passageiros_iniciais_esperando


    # --- Lógica de Embarque (Nova abordagem baseada na fila) ---
    def processar_fila_embarque(self):
        """
        Processa a fila de espera, tentando embarcar o primeiro passageiro 'esperando'
        em qualquer autocarro estacionado da cor correspondente com espaço.
        Repete o processo enquanto for possível embarcar passageiros.
        Remove autocarros cheios da área de estacionamento.
        """
        print("\n--- A processar fila de espera e embarque em autocarros estacionados ---")
        embarque_realizado_nesta_iteracao_geral = True # Flag para continuar processando a fila enquanto houver embarques

        while embarque_realizado_nesta_iteracao_geral:
            embarque_realizado_nesta_iteracao_geral = False # Reseta a flag para esta iteração do loop WHILE

            # 1. Encontrar o primeiro passageiro que ainda está esperando na fila original (mantendo a ordem original da fila_aleatoria)
            primeiro_passageiro_esperando = None
            for passenger in self.fila_aleatoria:
                if passenger.estado == 'esperando':
                    primeiro_passageiro_esperando = passenger
                    break # Encontrou o primeiro passageiro 'esperando', sai deste FOR loop

            if primeiro_passageiro_esperando:
                cor_passageiro = primeiro_passageiro_esperando.cor
                print(f" -> Primeiro passageiro esperando: {primeiro_passageiro_esperando} (Cor: {cor_passageiro})")

                # 2. Procurar por QUALQUER autocarro estacionado da cor do passageiro com espaço
                autocarro_disponivel = None
                # Iterar sobre os autocarros estacionados da cor do passageiro
                for bus in self.estacionamento_por_cor.get(cor_passageiro, []):
                    if len(bus.passageiros_embarcados) < bus.capacidade:
                        autocarro_disponivel = bus
                        break # Encontrou o primeiro autocarro disponível com espaço, pode usar este e sair deste FOR loop

                if autocarro_disponivel:
                    # 3. Embarcar o passageiro no autocarro encontrado
                    print(f" -> Encontrado autocarro disponível: {autocarro_disponivel.cor} (Embarcados: {len(autocarro_disponivel.passageiros_embarcados)}/{autocarro_disponivel.capacidade})")
                    primeiro_passageiro_esperando.embarcar() # Muda o estado do passageiro globalmente para 'embarcado'
                    autocarro_disponivel.passageiros_embarcados.append(primeiro_passageiro_esperando) # Adiciona a referência do passageiro à lista interna do autocarro
                    print(f" -> Passageiro {primeiro_passageiro_esperando.cor} embarcado no autocarro {autocarro_disponivel.cor}.")
                    print(f" -> Autocarro {autocarro_disponivel.cor} agora com {len(autocarro_disponivel.passageiros_embarcados)}/{autocarro_disponivel.capacidade} passageiros.")

                    # Marcamos que um embarque foi realizado, para que o loop WHILE principal continue na próxima iteração
                    embarque_realizado_nesta_iteracao_geral = True

                    # O loop WHILE irá agora recomeçar, e na próxima iteração,
                    # o `primeiro_passageiro_esperando` encontrado será o próximo passageiro
                    # na fila_aleatoria que ainda está no estado 'esperando'.

                    # 4. Verificar se o autocarro ficou cheio após este embarque (para possível remoção visual depois)
                    if len(autocarro_disponivel.passageiros_embarcados) >= autocarro_disponivel.capacidade:
                        print(f" -> Autocarro {autocarro_disponivel.cor} ficou cheio.")
                        # A remoção efetiva dos autocarros cheios da lista de estacionamento
                        # acontecerá no final da função, após o loop WHILE principal terminar.

                else:
                    # 4. Se não houver autocarro disponível para o primeiro passageiro 'esperando' da fila
                    print(f" -> Nenhum autocarro estacionado {cor_passageiro} com espaço disponível para o primeiro passageiro esperando. Parando processamento da fila nesta tentativa.")
                    # A flag 'embarque_realizado_nesta_iteracao_geral' permanece False,
                    # o que fará com que o loop WHILE termine se nenhum outro embarque for feito nesta iteração.

            else:
                # Se não há passageiros 'esperando' em toda a fila_aleatoria
                print(" -> Não há passageiros esperando na fila.")
                break # Sai do loop WHILE principal se não há mais passageiros esperando em toda a fila.

        # Fim do loop WHILE. Agora, remover os autocarros cheios da área de estacionamento.
        autocarros_a_manter_por_cor = {}
        autocarros_removidos_total = 0
        for cor, lista_autocarros in list(self.estacionamento_por_cor.items()): # Usar list() para poder modificar o dicionário
             autocarros_a_manter = []
             for bus in lista_autocarros:
                 if len(bus.passageiros_embarcados) < bus.capacidade:
                     autocarros_a_manter.append(bus)
                 else:
                     # Este autocarro está cheio, não o adicionamos à lista a manter.
                     # Ele será implicitamente removido da área de estacionamento lógica.
                     print(f" -> Removendo autocarro {bus.cor} cheio da área de estacionamento.")
                     autocarros_removidos_total += 1

             autocarros_a_manter_por_cor[cor] = autocarros_a_manter

        self.estacionamento_por_cor = autocarros_a_manter_por_cor
        if autocarros_removidos_total > 0:
             print(f"Total de {autocarros_removidos_total} autocarros cheios removidos da área de estacionamento.")


        print("--- Processamento da fila de espera e estacionamento concluído ---")

        # Verifica condição de vitória após processar a fila e estacionamento
        # A JogoGUI chamará verificar_vitoria após o redesenho.
        # if self.verificar_vitoria():
        #      print("VITÓRIA alcançada após processamento da fila!")
        #      # A JogoGUI tratará da mensagem e reinício


    # --- Remoção de Autocarro ---
    # Modificada para apenas remover do tabuleiro principal e adicionar ao estacionamento
    def remove_bus(self, autocarro_a_remover: Autocarro):
        """Remove um autocarro do tabuleiro lógico e, se for de cor ativa, adiciona-o ao estacionamento por cor."""
        if autocarro_a_remover in self.tabuleiro.autocarros:
            print(f"Removendo autocarro {autocarro_a_remover.cor} do tabuleiro lógico...")
            self.tabuleiro.autocarros.remove(autocarro_a_remover)

            # Se a cor do autocarro for ativa, adiciona-o à área de estacionamento por cor
            if autocarro_a_remover.cor in self.cores_ativas:
                # Adiciona o autocarro à lista correspondente no dicionário de estacionamento
                # Inicializa a lista de passageiros embarcados para este autocarro
                autocarro_a_remover.passageiros_embarcados = []
                if autocarro_a_remover.cor not in self.estacionamento_por_cor:
                    # Isso não deve acontecer se o dicionário for inicializado corretamente com cores ativas,
                    # mas é uma salvaguarda.
                    print(f"Aviso: Cor {autocarro_a_remover.cor} não encontrada no dicionário de estacionamento. Inicializando.")
                    self.estacionamento_por_cor[autocarro_a_remover.cor] = []

                self.estacionamento_por_cor[autocarro_a_remover.cor].append(autocarro_a_remover)
                print(f"Autocarro {autocarro_a_remover.cor} adicionado à área de estacionamento por cor.")
            else:
                # Se for um autocarro bloqueador, ele simplesmente desaparece
                print(f"Autocarro bloqueador {autocarro_a_remover.cor} REMOVIDO do tabuleiro lógico (não estacionado na área por cor).")

            print(f"Autocarro {autocarro_a_remover.cor} REMOVIDO do tabuleiro lógico.")
            return True
        else:
            print(f"Aviso: Tentativa remover autocarro {autocarro_a_remover.cor} não encontrado no tabuleiro.")
            return False

    # --- Condição de Vitória ---
    def verificar_vitoria(self):
        """Verifica se a condição de vitória foi atingida (todos os passageiros embarcados)."""
        # A condição de vitória permanece a mesma: verificar se *todos* os passageiros
        # na lista total de passageiros (self.passageiros) têm o estado 'embarcado'.

        if not self.passageiros:
             # Se não há passageiros no total, não há vitória (ou é um estado inicial inválido)
             return False

        # Verifica se o estado de *todos* os passageiros é 'embarcado'
        all_embarked = all(p.estado == 'embarcado' for p in self.passageiros)

        if all_embarked:
            # Verifica se AINDA HÁ autocarros de cor ativa estacionados que não estão cheios
            # Embora a condição de vitória seja apenas passageiros, pode ser útil para debug.
            # if any(len(bus.passageiros_embarcados) < bus.capacidade for cor in self.cores_ativas for bus in self.estacionamento_por_cor.get(cor, [])):
            #      print("DEBUG (verificar_vitoria): Todos os passageiros embarcados, mas ainda há autocarros de cor ativa estacionados não cheios.")
            print("VITÓRIA: Todos os passageiros embarcados!");
            return True
        else:
            # Opcional: para debug, verificar se há passageiros ainda esperando
            # any_waiting = any(p.estado == 'esperando' for p in self.passageiros)
            # if any_waiting:
            #     print(f"DEBUG (verificar_vitoria): Ainda há passageiros esperando.")
            return False # Condição de vitória não satisfeita

# ... (Resto do código do jogo.py, como a parte do __main__)