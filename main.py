from ursina import *
from ursina.shaders import basic_lighting_shader
import math

application.development_mode = False

app = Ursina()

# Entidades
pista = Entity(
    model='modelos/pista.glb', 
    shader=basic_lighting_shader,
    scale=2.5, 
    position=(0, -0.25, 15),
    rotation_y=180
)

chao = Entity(
    model='plane', 
    scale=(100, 1, 100), 
    shader=basic_lighting_shader,
    position=(0, -5, 0),
    color=color.dark_gray
)

bola = Entity(
    model='modelos/bola.glb',
    scale=0.5, 
    shader=basic_lighting_shader,
    position=(0, 0.5, 2),
    collider='sphere'
)

seta_pivo = Entity(position=(0, 0.5, 2)) 

corpo_seta = Entity(
    parent=seta_pivo,
    model='cube',
    color=color.green,
    scale=(0.1, 0.05, 1.5),
    position=(0, 0, 0.75)
)

ponta_seta = Entity(
    parent=seta_pivo,
    model='arrow',
    color=color.green,
    scale=(0.6, 0.6, 0.6),
    position=(0, 0, 2.3), # Posicionado exatamente após o fim do corpo da seta
    rotation_x=90,        # Deita a seta na pista
    rotation_z=90         # Aponta ela para frente (eixo Z positivo)
)

# Lista para armazenar os pinos
pinos = []

# Posições dos pinos em formato de triângulo (X, Z)
posicoes_pinos = [
    (0, 22),       
    (-0.5, 23), (0.5, 23), 
    (-1, 24), (0, 24), (1, 24),
    (-1.5, 25), (-0.5, 25), (0.5, 25), (1.5, 25)
]

# Interface de Texto (Placar)
texto_placar = Text(text='', position=(-0.2, 0.3), scale=2, color=color.yellow)
texto_instrucoes = Text(text='Espaco: Lancar na direcao da seta | R: Reiniciar', position=(-0.85, 0.45), scale=1)

def criar_pinos():
    for p in pinos:
        destroy(p)
    pinos.clear()
    
    for pos in posicoes_pinos:
        pino = Entity(
            model='modelos/pino.glb',  # Substitua por 'pino.obj' quando quiser usar seu modelo,
            shader=basic_lighting_shader,
            scale=0.45, 
            position=(pos[0], 0.3, pos[1]), 
            collider='box'
        )
        pino.velocidade_x = 0
        pino.velocidade_z = 0
        pino.rotacao_x = 0
        pino.derrubado = False 
        pinos.append(pino)

# Cria os pinos inicialmente
criar_pinos()

# --- LÓGICA DE JOGO E FÍSICA ---

bola_lancada = False
velocidade_bola = 30
jogada_finalizada = False

# Variáveis para o cálculo do vetor de movimento
vel_x = 0
vel_z = 0

def update():
    global bola_lancada, jogada_finalizada, vel_x, vel_z
    
    # Oscilação periódica da seta antes do lançamento
    if not bola_lancada and not jogada_finalizada:
        # Usa a função Seno baseada no tempo para girar suavemente entre -25 e +25 graus
        seta_pivo.rotation_y = math.sin(time.time() * 3) * 25
        
        if held_keys['space']:
            bola_lancada = True
            
            # Converte o ângulo atual da seta (Y) de graus para radianos
            angulo_rad = math.radians(seta_pivo.rotation_y)
            
            # Calcula a velocidade decomposta em X e Z usando Trigonometria
            vel_x = math.sin(angulo_rad) * velocidade_bola
            vel_z = math.cos(angulo_rad) * velocidade_bola
            
            # Esconde a seta após o lançamento
            seta_pivo.enabled = False
            
    # Movimento angular da bola após o lançamento
    if bola_lancada and bola.enabled:
        bola.x += vel_x * time.dt
        bola.z += vel_z * time.dt

        # Gira o eixo X baseado na velocidade atual (vel_z) multiplicada por um fator (ex: 20)
        bola.rotation_x += vel_z * 20 * time.dt
        
        # Se a bola passar do limite de fundo da pista ou sair pelas laterais (valeta)
        if bola.z > 29 or abs(bola.x) > 3:
            bola.enabled = False 
            bola_lancada = False
            jogada_finalizada = True
            calcular_placar()
        
        # Verifica colisão da bola com cada pino
        for pino in pinos:
            if distance(bola, pino) < 0.8 and pino.velocidade_z == 0:
                # Transfere a velocidade da bola para o pino
                pino.velocidade_z = vel_z * 0.8
                pino.velocidade_x = vel_x * 0.8 + (pino.x - bola.x) * 10
                
                # A bola perde um pouco de força no impacto
                vel_z *= 0.6
                vel_x *= 0.6

    # Atualiza a física dos pinos
    for pino in pinos:
        if pino.velocidade_z != 0 or pino.velocidade_x != 0:
            pino.z += pino.velocidade_z * time.dt
            pino.x += pino.velocidade_x * time.dt
            
            if pino.rotacao_x < 90:
                pino.rotacao_x += 400 * time.dt
                pino.rotation_x = pino.rotacao_x
                pino.y = max(0.1, pino.y - 2 * time.dt)
                
                if pino.rotacao_x > 30:
                    pino.derrubado = True
            
            pino.velocidade_z *= 0.96
            pino.velocidade_x *= 0.96
            
            # Efeito dominó
            for outro_pino in pinos:
                if outro_pino != pino and distance(pino, outro_pino) < 0.6:
                    if outro_pino.velocidade_z == 0:
                        outro_pino.velocidade_z = pino.velocidade_z * 0.8
                        outro_pino.velocidade_x = pino.velocidade_x * 0.8 + (outro_pino.x - pino.x) * 8
                        pino.velocidade_z *= 0.5

def calcular_placar():
    pinos_derrubados = sum(1 for pino in pinos if pino.derrubado)
    if pinos_derrubados == 10:
        texto_placar.text = f"STRIKE! \nVoce derrubou todos os 10!"
    else:
        texto_placar.text = f"FIM DA JOGADA\nPinos derrubados: {pinos_derrubados}"

# Detecta teclas
def input(key):
    global bola_lancada, jogada_finalizada, vel_x, vel_z

    if key == 'escape':
        application.quit()

    if key == 'r':
        bola.position = (0, 0.5, 2)
        bola.enabled = True
        bola_lancada = False
        jogada_finalizada = False
        vel_x, vel_z = 0, 0
        
        # Reseta e reativa a seta de mira
        seta_pivo.rotation_y = 0
        seta_pivo.enabled = True
        
        texto_placar.text = ""
        criar_pinos()

# Configuração da câmera
camera.position = (0, 6, -12)
camera.rotation_x = 15

app.run()