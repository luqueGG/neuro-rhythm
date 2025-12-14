import cv2
import pygame
import numpy as np
from ultralytics import YOLO
import sys
import random
import math
import os

#CONFIGURACION GENERAL
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
CAMERA_ID = 0 

# RUTA DE MUSICA 
MUSIC_PATH = "music/background.mp3" 
SPAWN_INTERVAL = 45  # Frames entre objetivos
TARGET_SPEED = 9
ACTIVATION_ZONE_X = 350
PERFECT_ZONE_X = 250
TARGET_WIDTH = 140
TARGET_HEIGHT = 90

# Paleta de Colores (Cyberpunk / Neon)
COLOR_BG = (15, 23, 42)          # Azul oscuro solido
COLOR_ACCENT = (0, 255, 157)     # Verde Neon
COLOR_SECONDARY = (67, 97, 238)  # Azul Neon
COLOR_DANGER = (255, 50, 80)     # Rojo Neon
COLOR_WHITE = (240, 240, 240)
COLOR_BLACK = (0, 0, 0)
COLOR_TEXT_DIM = (148, 163, 184)
COLOR_GOLD = (255, 215, 0)

#MOTOR DE CAMARA
class CameraEngine:
    def __init__(self):
        try:
            self.cap = cv2.VideoCapture(CAMERA_ID)
            if not self.cap.isOpened():
                raise RuntimeError(f"No se pudo abrir la camara {CAMERA_ID}")
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)
            self.last_frame_rgb = None
            print("Camara iniciada correctamente")
        except Exception as e:
            print(f"Error al iniciar camara: {e}")
            raise

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Warning: No se pudo leer frame de la camara")
            return None
        
        # Efecto Espejo
        frame = cv2.flip(frame, 1)
        
        self.last_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = np.transpose(self.last_frame_rgb, (1, 0, 2))
        return pygame.surfarray.make_surface(frame_surface)

    def release(self):
        if self.cap:
            self.cap.release()
            print("Camara liberada")

#RITMO
class LevelBody:
    def __init__(self, screen, model):
        self.screen = screen
        self.model = model
        self.font = pygame.font.SysFont("Arial", 36, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 24)
        
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.multiplier = 1
        self.targets = []
        self.spawn_timer = 0
        self.spawn_count = 0
        
        # Estadisticas
        self.hits = 0
        self.misses = 0
        
        # Efectos visuales
        self.feedback_messages = []  # Para mostrar +puntos, MISS, etc.
        
        # Tipos de poses y colores
        self.pose_names = [
            "BRAZOS ARRIBA",      # 0
            "BRAZO DERECHO ->",   # 1
            "BRAZO IZQUIERDO <-", # 2
            "BRAZOS ABAJO",       # 3
            "MODO X (CRUZADOS)"   # 4
        ]
        self.pose_colors = [
            (255, 255, 0),    # Amarillo
            (255, 100, 100),  # Rojo claro
            (100, 100, 255),  # Azul claro
            (255, 0, 255),    # Magenta
            (0, 255, 255)     # Cyan
        ]

    def detect_active_poses(self, keypoints):
        """
        Devuelve una lista de TODAS las poses detectadas simultaneamente.
        """
        active_poses = set()
        
        if len(keypoints) < 13:
            return active_poses
        
        # Extraer puntos clave (YOLO Format)
        ls = keypoints[5]   # Hombro Izq
        rs = keypoints[6]   # Hombro Der
        lw = keypoints[9]   # Muneca Izq
        rw = keypoints[10]  # Muneca Der

        # Validar que los puntos existan
        if lw[0] == 0 or rw[0] == 0 or ls[0] == 0 or rs[0] == 0:
            return active_poses

        # --- PARAMETROS DE DETECCION ---
        y_dist_vert = 60   # Umbral para arriba/abajo
        x_dist_ext = 30    # Umbral minimo de extension lateral
        y_tol_side = 200   # Tolerancia vertical para brazos laterales

        # POSE 4: MODO X (Brazos Cruzados)
        arms_crossed = (lw[0] > rw[0]) and (lw[1] > ls[1]) and (rw[1] > rs[1])
        if arms_crossed:
            active_poses.add(4)

        # POSE 0: Brazos Arriba
        left_is_up = lw[1] < ls[1] - y_dist_vert
        right_is_up = rw[1] < rs[1] - y_dist_vert
        if left_is_up and right_is_up:
            active_poses.add(0)
            
        # POSE 3: Brazos Abajo
        left_is_down = lw[1] > ls[1] + y_dist_vert
        right_is_down = rw[1] > rs[1] + y_dist_vert
        if left_is_down and right_is_down:
            active_poses.add(3)

        # POSE 1: Brazo Derecho Extendido
        right_is_side = (rw[0] > rs[0] + x_dist_ext) and (abs(rw[1] - rs[1]) < y_tol_side)
        if right_is_side:
            active_poses.add(1)
            
        # POSE 2: Brazo Izquierdo Extendido
        left_is_side = (lw[0] < ls[0] - x_dist_ext) and (abs(lw[1] - ls[1]) < y_tol_side)
        if left_is_side:
            active_poses.add(2)
        
        return active_poses

    def spawn_target(self):
        pose_type = random.randint(0, 4)
        y = random.randint(150, WINDOW_HEIGHT - 150)
        
        self.targets.append({
            "x": WINDOW_WIDTH,
            "y": y,
            "type": pose_type,
            "width": TARGET_WIDTH,
            "height": TARGET_HEIGHT,
            "speed": TARGET_SPEED,
            "id": self.spawn_count,
            "checked": False  # Para evitar multiples evaluaciones
        })
        self.spawn_count += 1

    def add_feedback(self, text, x, y, color, size=36):
        """Anade un mensaje de feedback temporal"""
        self.feedback_messages.append({
            "text": text,
            "x": x,
            "y": y,
            "color": color,
            "size": size,
            "lifetime": 30  # Frames que durara visible
        })

    def update(self, frame_rgb):
        # 1. Inferencia YOLO con manejo de errores
        try:
            results = self.model(frame_rgb, stream=True, verbose=False, conf=0.5)
            keypoints = []
            for r in results:
                if r.keypoints and len(r.keypoints.xy) > 0:
                    keypoints = r.keypoints.xy[0].cpu().numpy()
                    break
        except Exception as e:
            print(f"Error en inferencia YOLO: {e}")
            keypoints = []

        # 2. Detectar todas las poses activas
        active_poses = self.detect_active_poses(keypoints)

        # 3. Generar nuevos objetivos
        self.spawn_timer += 1
        if self.spawn_timer >= SPAWN_INTERVAL:
            self.spawn_target()
            self.spawn_timer = 0

        # 4. Mover y evaluar objetivos
        to_remove = []
        
        for target in self.targets:
            target["x"] -= target["speed"]
            
            # Si cruzo la zona de activacion y aun no fue checkeado
            if target["x"] < ACTIVATION_ZONE_X and not target["checked"]:
                target["checked"] = True
                
                # Verificar si la pose correcta esta activa
                if target["type"] in active_poses:
                    # ACIERTO
                    if target["x"] > PERFECT_ZONE_X:
                        points = 100
                        feedback = "PERFECT!"
                        color = COLOR_GOLD
                    else:
                        points = 50
                        feedback = "GOOD"
                        color = COLOR_ACCENT
                    
                    self.score += points * self.multiplier
                    self.combo += 1
                    self.hits += 1
                    
                    if self.combo > self.max_combo:
                        self.max_combo = self.combo
                    
                    # Actualizar multiplicador
                    if self.combo >= 20:
                        self.multiplier = 4
                    elif self.combo >= 10:
                        self.multiplier = 2
                    
                    self.add_feedback(f"+{points * self.multiplier}", target["x"], target["y"], color)
                else:
                    # FALLO
                    self.combo = 0
                    self.multiplier = 1
                    self.misses += 1
                    self.add_feedback("MISS!", target["x"], target["y"], COLOR_DANGER)
            
            # Marcar para eliminar si sale de pantalla
            if target["x"] < -target["width"]:
                to_remove.append(target)
        
        # Eliminar targets fuera de pantalla
        for target in to_remove:
            self.targets.remove(target)
        
        # 5. Actualizar mensajes de feedback
        for msg in self.feedback_messages[:]:
            msg["lifetime"] -= 1
            msg["y"] -= 2  # Hacer que suba
            if msg["lifetime"] <= 0:
                self.feedback_messages.remove(msg)

        # 6. Dibujar UI (ARRIBA de todo)
        self.draw_ui(active_poses)

    def draw_ui(self, active_poses):
        """Dibuja interfaz del juego"""
        # Panel superior con estadisticas (PANEL COMPACTO Y ALTO)
        panel_height = 80
        panel = pygame.Surface((WINDOW_WIDTH, panel_height))
        panel.set_alpha(200)
        panel.fill((10, 15, 30))
        self.screen.blit(panel, (0, 0))
        
        # Linea decorativa inferior del panel
        pygame.draw.line(self.screen, COLOR_ACCENT, (0, panel_height), (WINDOW_WIDTH, panel_height), 3)
        
        # Score (Izquierda)
        score_txt = self.font.render(f"SCORE: {self.score}", True, COLOR_WHITE)
        self.screen.blit(score_txt, (20, 15))
        
        # Combo (Centro)
        combo_color = COLOR_ACCENT if self.combo > 0 else COLOR_TEXT_DIM
        combo_txt = self.font.render(f"COMBO: {self.combo}x", True, combo_color)
        combo_rect = combo_txt.get_rect(center=(WINDOW_WIDTH//2, 40))
        self.screen.blit(combo_txt, combo_rect)
        
        # Multiplicador (Derecha)
        mult_txt = self.font.render(f"x{self.multiplier}", True, COLOR_GOLD)
        mult_rect = mult_txt.get_rect(right=WINDOW_WIDTH - 20, top=15)
        self.screen.blit(mult_txt, mult_rect)
        
        # Indicador de poses activas (LADO IZQUIERDO, DEBAJO DEL PANEL)
        pose_y_start = panel_height + 20
        for i, pose_name in enumerate(self.pose_names):
            is_active = i in active_poses
            color = self.pose_colors[i] if is_active else COLOR_TEXT_DIM
            
            # Fondo de la etiqueta de pose
            pose_bg = pygame.Surface((200, 35))
            pose_bg.set_alpha(180 if is_active else 100)
            pose_bg.fill((20, 25, 40))
            self.screen.blit(pose_bg, (10, pose_y_start + i * 40))
            
            # Borde lateral si está activa
            if is_active:
                pygame.draw.rect(self.screen, color, (10, pose_y_start + i * 40, 5, 35))
            
            # Texto de la pose
            pose_txt = self.small_font.render(pose_name, True, color)
            self.screen.blit(pose_txt, (20, pose_y_start + i * 40 + 5))
        
        # Zonas de activacion (Derecha, vertical)
        # Zona PERFECT
        perfect_zone = pygame.Rect(PERFECT_ZONE_X, panel_height + 20, 8, WINDOW_HEIGHT - panel_height - 40)
        pygame.draw.rect(self.screen, COLOR_GOLD, perfect_zone)
        perfect_label = self.small_font.render("PERFECT", True, COLOR_GOLD)
        perfect_label = pygame.transform.rotate(perfect_label, 90)
        self.screen.blit(perfect_label, (PERFECT_ZONE_X - 30, WINDOW_HEIGHT//2 - 40))
        
        # Zona GOOD
        good_zone = pygame.Rect(ACTIVATION_ZONE_X, panel_height + 20, 8, WINDOW_HEIGHT - panel_height - 40)
        pygame.draw.rect(self.screen, COLOR_ACCENT, good_zone)
        good_label = self.small_font.render("GOOD", True, COLOR_ACCENT)
        good_label = pygame.transform.rotate(good_label, 90)
        self.screen.blit(good_label, (ACTIVATION_ZONE_X - 30, WINDOW_HEIGHT//2 - 20))
        
        # Dibujar objetivos
        for target in self.targets:
            color = self.pose_colors[target["type"]]
            
            # Sombra
            shadow_rect = pygame.Rect(target["x"] + 5, target["y"] + 5, target["width"], target["height"])
            shadow = pygame.Surface((target["width"], target["height"]))
            shadow.set_alpha(80)
            shadow.fill(COLOR_BLACK)
            self.screen.blit(shadow, (shadow_rect.x, shadow_rect.y))
            
            # Target principal
            target_rect = pygame.Rect(target["x"], target["y"], target["width"], target["height"])
            pygame.draw.rect(self.screen, color, target_rect, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_WHITE, target_rect, 3, border_radius=10)
            
            # Texto del target
            txt = self.small_font.render(self.pose_names[target["type"]], True, COLOR_BLACK)
            txt_rect = txt.get_rect(center=target_rect.center)
            self.screen.blit(txt, txt_rect)
        
        # Mensajes de feedback
        for msg in self.feedback_messages:
            alpha = int(255 * (msg["lifetime"] / 30))
            feedback_font = pygame.font.SysFont("Arial", msg["size"], bold=True)
            txt_surf = feedback_font.render(msg["text"], True, msg["color"])
            txt_surf.set_alpha(alpha)
            self.screen.blit(txt_surf, (msg["x"], msg["y"]))

#MENU PRINCIPAL 
class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("Arial", 80, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 28)
        self.btn_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.info_font = pygame.font.SysFont("Arial", 20)
        
        # Animaciones
        self.time = 0
        self.particles = []
        
        btn_width = 300
        btn_height = 70
        btn_spacing = 30
        start_y = 320
        
        self.buttons = [
            {
                "text": "NIVEL 1: RITMO",
                "rect": pygame.Rect(
                    WINDOW_WIDTH // 2 - btn_width // 2,
                    start_y,
                    btn_width,
                    btn_height
                ),
                "action": "lvl1",
                "color": COLOR_ACCENT
            },
            {
                "text": "SALIR",
                "rect": pygame.Rect(
                    WINDOW_WIDTH // 2 - btn_width // 2,
                    start_y + btn_height + btn_spacing,
                    btn_width,
                    btn_height
                ),
                "action": "quit",
                "color": COLOR_DANGER
            }
        ]
        
        # Inicializar particulas
        for _ in range(30):
            self.particles.append({
                "x": random.randint(0, WINDOW_WIDTH),
                "y": random.randint(0, WINDOW_HEIGHT),
                "speed": random.uniform(0.5, 2),
                "size": random.randint(1, 3)
            })

    def draw_animated_background(self):
        """Fondo animado con particulas"""
        self.screen.fill(COLOR_BG)
        
        # Actualizar y dibujar particulas
        for p in self.particles:
            p["y"] += p["speed"]
            if p["y"] > WINDOW_HEIGHT:
                p["y"] = 0
                p["x"] = random.randint(0, WINDOW_WIDTH)
            
            alpha = int(150 + 105 * math.sin(self.time * 0.02 + p["x"]))
            color = (*COLOR_ACCENT, alpha)
            pygame.draw.circle(self.screen, COLOR_ACCENT, (int(p["x"]), int(p["y"])), p["size"])

    def draw_title_section(self):
        """Dibuja el titulo con efectos (SIN superposicion)"""
        # Titulo principal con efecto de brillo
        title_text = "NEURO RHYTHM"
        
        # Sombra del titulo
        shadow_surf = self.title_font.render(title_text, True, COLOR_BLACK)
        shadow_rect = shadow_surf.get_rect(center=(WINDOW_WIDTH//2 + 4, 120))
        self.screen.blit(shadow_surf, shadow_rect)
        
        # Titulo con gradiente (simulado con capas)
        title_surf = self.title_font.render(title_text, True, COLOR_ACCENT)
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 116))
        self.screen.blit(title_surf, title_rect)
        
        # Subtitulo
        subtitle_text = "Sistema de Deteccion de Movimiento"
        subtitle_surf = self.subtitle_font.render(subtitle_text, True, COLOR_TEXT_DIM)
        subtitle_rect = subtitle_surf.get_rect(center=(WINDOW_WIDTH//2, 180))
        self.screen.blit(subtitle_surf, subtitle_rect)
        
        # Linea decorativa
        line_width = 400
        line_y = 210
        pygame.draw.line(
            self.screen,
            COLOR_SECONDARY,
            (WINDOW_WIDTH//2 - line_width//2, line_y),
            (WINDOW_WIDTH//2 + line_width//2, line_y),
            3
        )

    def draw_feature_cards(self):
        """Cards con caracteristicas (REPOSICIONADAS debajo de botones)"""
        features = [
            "Deteccion en Tiempo Real",
            "Sistema de Combos",
            "Multiples Poses"
        ]
        
        card_width = 200
        card_height = 60
        start_y = 540  # Más abajo para evitar conflicto con botones
        spacing = 40
        total_width = (card_width * 3) + (spacing * 2)
        start_x = (WINDOW_WIDTH - total_width) // 2
        
        for i, feature in enumerate(features):
            x = start_x + (card_width + spacing) * i
            
            card_rect = pygame.Rect(x, start_y, card_width, card_height)
            
            # Sombra
            shadow_rect = pygame.Rect(x + 4, start_y + 4, card_width, card_height)
            pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow_rect, border_radius=10)
            
            # Card principal
            pygame.draw.rect(self.screen, (30, 41, 59), card_rect, border_radius=10)
            pygame.draw.rect(self.screen, (67, 97, 238), card_rect, 2, border_radius=10)
            
            # Texto
            feature_surf = self.info_font.render(feature, True, COLOR_WHITE)
            feature_rect = feature_surf.get_rect(center=card_rect.center)
            self.screen.blit(feature_surf, feature_rect)

    def draw_buttons(self):
        """Dibuja botones interactivos mejorados"""
        mouse_pos = pygame.mouse.get_pos()
        
        for i, btn in enumerate(self.buttons):
            rect = btn["rect"]
            hover = rect.collidepoint(mouse_pos)
            
            # Efecto de elevacion en hover
            if hover:
                # Sombra mas pronunciada
                shadow_rect = pygame.Rect(rect.x + 6, rect.y + 6, rect.width, rect.height)
                pygame.draw.rect(self.screen, (0, 0, 0, 150), shadow_rect, border_radius=15)
                
                # Animacion de escala
                scale_offset = int(5 * math.sin(self.time * 0.2))
                display_rect = pygame.Rect(
                    rect.x - scale_offset//2, 
                    rect.y - scale_offset//2,
                    rect.width + scale_offset, 
                    rect.height + scale_offset
                )
            else:
                # Sombra sutil
                shadow_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.width, rect.height)
                pygame.draw.rect(self.screen, (0, 0, 0, 80), shadow_rect, border_radius=15)
                display_rect = rect
            
            # Colores segun hover
            if hover:
                bg_color = btn["color"]
                border_color = COLOR_WHITE
                text_color = COLOR_BLACK if btn["action"] == "lvl1" else COLOR_WHITE
                
                # Efecto de brillo pulsante
                glow = int(20 * (1 + math.sin(self.time * 0.15)))
                bg_color = tuple(min(255, c + glow) for c in bg_color)
            else:
                bg_color = (30, 41, 59)
                border_color = btn["color"]
                text_color = btn["color"]
            
            # Dibujar boton
            pygame.draw.rect(self.screen, bg_color, display_rect, border_radius=15)
            pygame.draw.rect(self.screen, border_color, display_rect, 4, border_radius=15)
            
            # Barra decorativa lateral
            if hover:
                bar_rect = pygame.Rect(display_rect.x + 10, display_rect.y + 20, 
                                      5, display_rect.height - 40)
                pygame.draw.rect(self.screen, text_color, bar_rect, border_radius=3)
            
            # Texto del boton
            txt_surf = self.btn_font.render(btn["text"], True, text_color)
            txt_rect = txt_surf.get_rect(center=display_rect.center)
            self.screen.blit(txt_surf, txt_rect)
            
            # Indicador de hover (flecha animada)
            if hover:
                arrow_x = display_rect.right - 40
                arrow_y = display_rect.centery
                offset = int(5 * math.sin(self.time * 0.3))
                
                points = [
                    (arrow_x + offset, arrow_y),
                    (arrow_x - 10 + offset, arrow_y - 8),
                    (arrow_x - 10 + offset, arrow_y + 8)
                ]
                pygame.draw.polygon(self.screen, text_color, points)

    def draw(self):
        """Dibuja el menu completo"""
        self.time += 1
        
        # 1. Fondo animado
        self.draw_animated_background()
        
        # 2. Titulo con efectos
        self.draw_title_section()
        
        # 3. Botones principales
        self.draw_buttons()
        
        # 4. Cards de caracteristicas
        self.draw_feature_cards()
        
        # 5. Footer con creditos
        footer_text = "Presiona un boton para comenzar"
        footer_surf = self.info_font.render(footer_text, True, COLOR_TEXT_DIM)
        alpha = int(200 + 55 * math.sin(self.time * 0.05))
        footer_surf.set_alpha(alpha)
        self.screen.blit(footer_surf, (WINDOW_WIDTH//2 - footer_surf.get_width()//2, WINDOW_HEIGHT - 30))

    def check_click(self, pos):
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos):
                return btn["action"]
        return None

#GESTOR PRINCIPAL
class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("NEURO RHYTHM - Proyecto Final")
        self.clock = pygame.time.Clock()
        
        print("\n" + "="*50)
        print("NEURO RHYTHM - Sistema Iniciando...")
        print("="*50)
        
        # Inicializar sistema de audio
        pygame.mixer.init()
        self.music_loaded = False
        self.load_music()
        
        try:
            print("Cargando Modelo YOLO...")
            self.yolo_model = YOLO("yolov8n-pose.pt")
            print("Modelo YOLO cargado")
            
            print("Iniciando Camara...")
            self.cam = CameraEngine()
            
            print("Sistema listo para jugar")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"Error critico al inicializar: {e}")
            sys.exit(1)
        
        self.state = "MENU"
        self.menu = MainMenu(self.screen)
        self.level = None

    def load_music(self):
        """Carga y reproduce la musica de fondo"""
        try:
            if os.path.exists(MUSIC_PATH):
                pygame.mixer.music.load(MUSIC_PATH)
                pygame.mixer.music.set_volume(0.5)  # Volumen al 50%
                pygame.mixer.music.play(-1)  # Loop infinito
                self.music_loaded = True
                print(f"Musica cargada: {MUSIC_PATH}")
            else:
                print(f"ADVERTENCIA: No se encontro el archivo de musica en: {MUSIC_PATH}")
                print("El juego funcionara sin musica de fondo.")
        except Exception as e:
            print(f"Error al cargar musica: {e}")
            print("El juego continuara sin musica de fondo.")

    def run(self):
        running = True
        
        try:
            while running:
                events = pygame.event.get()
                
                # ESTADO: MENU
                if self.state == "MENU":
                    self.menu.draw()
                    
                    for event in events:
                        if event.type == pygame.QUIT:
                            running = False
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            action = self.menu.check_click(event.pos)
                            if action == "quit":
                                running = False
                            elif action == "lvl1":
                                self.state = "GAME"
                                self.level = LevelBody(self.screen, self.yolo_model)
                                print("Iniciando Nivel 1: RITMO")

                # ESTADO: JUEGO
                elif self.state == "GAME":
                    # Obtener frame
                    frame_surf = self.cam.get_frame()
                    if frame_surf:
                        self.screen.blit(frame_surf, (0, 0))
                    
                    # Actualizar Nivel
                    if self.level and self.cam.last_frame_rgb is not None:
                        self.level.update(self.cam.last_frame_rgb)
                    
                    # Boton Volver
                    back_rect = pygame.Rect(10, WINDOW_HEIGHT - 50, 120, 40)
                    pygame.draw.rect(self.screen, COLOR_DANGER, back_rect, border_radius=8)
                    back_txt = pygame.font.SysFont("Arial", 20).render("SALIR (ESC)", True, COLOR_WHITE)
                    self.screen.blit(back_txt, (20, WINDOW_HEIGHT - 40))

                    # Eventos del Juego
                    for event in events:
                        if event.type == pygame.QUIT:
                            running = False
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            print(f"Partida terminada - Score: {self.level.score}, Max Combo: {self.level.max_combo}")
                            self.state = "MENU"
                            self.level = None

                pygame.display.flip()
                self.clock.tick(30)
                
        except KeyboardInterrupt:
            print("\nInterrupcion por teclado detectada")
        except Exception as e:
            print(f"\nError durante ejecucion: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Limpieza de recursos al cerrar"""
        print("\nLiberando recursos...")
        
        # Detener musica
        if self.music_loaded:
            pygame.mixer.music.stop()
            print("Musica detenida")
        
        if hasattr(self, 'cam'):
            self.cam.release()
        
        pygame.quit()
        print("Limpieza completada. Hasta pronto!")
        sys.exit(0)

if __name__ == "__main__":
    GameManager().run()
