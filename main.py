import cv2
import pygame
import numpy as np
from ultralytics import YOLO
import sys
import random
import math

# Intento de importar MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("ADVERTENCIA: MediaPipe no instalado. El Nivel 2 no funcionara.")

# ==========================================
# 1. CONFIGURACION GENERAL
# ==========================================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
CAMERA_ID = 0 

# Constantes de gameplay
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

# Colores para dedos (Nivel 2)
FINGER_COLORS = [
    (255, 0, 0),    # Pulgar (Rojo)
    (0, 255, 0),    # Indice (Verde)
    (0, 0, 255),    # Medio (Azul)
    (255, 255, 0),  # Anular (Amarillo)
    (255, 0, 255)   # Menique (Magenta)
]

# ==========================================
# 2. MOTOR DE CAMARA
# ==========================================
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
        
        # Guardar RGB para procesar (MediaPipe/YOLO)
        self.last_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convertir para Pygame (Rotar y Transponer)
        frame_surface = np.transpose(self.last_frame_rgb, (1, 0, 2))
        return pygame.surfarray.make_surface(frame_surface)

    def release(self):
        if self.cap:
            self.cap.release()
            print("Camara liberada")

# ==========================================
# 3. NIVEL 1: RITMO
# ==========================================
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

        # 2. Dibujar Esqueleto y Detectar Poses
        current_poses = set()
        if len(keypoints) > 0:
            self.draw_skeleton(keypoints)
            current_poses = self.detect_active_poses(keypoints)

        # 3. Logica de Spawn
        self.spawn_timer += 1
        if self.spawn_timer > SPAWN_INTERVAL: 
            self.spawn_target()
            self.spawn_timer = 0
            
        # 4. Dibujar Zonas de Activacion
        pygame.draw.rect(self.screen, (0, 255, 0, 50), (0, 0, ACTIVATION_ZONE_X, WINDOW_HEIGHT), 2)
        pygame.draw.line(self.screen, (255, 255, 0), (PERFECT_ZONE_X, 0), (PERFECT_ZONE_X, WINDOW_HEIGHT), 4)

        # 5. Actualizar Objetivos
        for target in self.targets[:]:
            target["x"] -= target["speed"]
            
            color = self.pose_colors[target["type"]]
            rect = pygame.Rect(
                target["x"] - target["width"]//2, 
                target["y"] - target["height"]//2,
                target["width"], 
                target["height"]
            )

            # Verificar si esta en la zona de activacion
            in_zone = target["x"] <= ACTIVATION_ZONE_X and target["x"] >= 50
            is_perfect = abs(target["x"] - PERFECT_ZONE_X) < 30
            
            # Dibujar el objetivo
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_WHITE, rect, 3, border_radius=10)
            
            # Texto de la pose
            pose_text = self.small_font.render(self.pose_names[target["type"]], True, COLOR_BLACK)
            text_rect = pose_text.get_rect(center=rect.center)
            self.screen.blit(pose_text, text_rect)
            
            # Zona jugador
            if in_zone and not target["checked"]:
                target["checked"] = True  # Marcar como evaluado
                
                # Verificar si el jugador esta haciendo la pose correcta
                if target["type"] in current_poses:
                    # ACIERTO
                    self.combo += 1
                    self.max_combo = max(self.max_combo, self.combo)
                    self.multiplier = 1 + (self.combo // 5)
                    
                    # Puntos extra por timing perfecto
                    points = 100 * self.multiplier
                    if is_perfect:
                        points = int(points * 1.5)
                        self.add_feedback("PERFECTO!", target["x"], target["y"] - 60, COLOR_GOLD, 40)
                    else:
                        self.add_feedback(f"+{points}", target["x"], target["y"] - 60, COLOR_ACCENT, 36)
                    
                    self.score += points
                    self.hits += 1
                    self.targets.remove(target)
                    
                    # Efecto visual de exito
                    pygame.draw.rect(self.screen, COLOR_ACCENT, rect, 0, border_radius=10)
                    
                else:
                    # FALLO (pose incorrecta)
                    self.combo = 0
                    self.multiplier = 1
                    self.misses += 1
                    self.targets.remove(target)
                    
                    # Efecto visual de error
                    center_x, center_y = rect.center
                    offset = 40
                    pygame.draw.line(self.screen, COLOR_DANGER, 
                                   (center_x - offset, center_y - offset), 
                                   (center_x + offset, center_y + offset), 10)
                    pygame.draw.line(self.screen, COLOR_DANGER, 
                                   (center_x - offset, center_y + offset), 
                                   (center_x + offset, center_y - offset), 10)
                    
                    self.add_feedback("MISS!", target["x"], target["y"] - 60, COLOR_DANGER, 40)
                    
            # Eliminar objetivos que salieron de la pantalla
            elif target["x"] < -100:
                if not target["checked"]:
                    self.combo = 0
                    self.multiplier = 1
                    self.misses += 1
                    self.add_feedback("PERDIDO", target["x"], target["y"], COLOR_TEXT_DIM, 30)
                self.targets.remove(target)

        # 6. Actualizar y dibujar mensajes de feedback
        for msg in self.feedback_messages[:]:
            msg["lifetime"] -= 1
            msg["y"] -= 2  # Flotar hacia arriba
            
            if msg["lifetime"] <= 0:
                self.feedback_messages.remove(msg)
            else:
                font = pygame.font.SysFont("Arial", msg["size"], bold=True)
                alpha = min(255, msg["lifetime"] * 8)  # Fade out
                text_surf = font.render(msg["text"], True, msg["color"])
                self.screen.blit(text_surf, (msg["x"] - text_surf.get_width()//2, msg["y"]))

        # 7. Dibujar UI
        self.draw_ui(current_poses)

    def draw_skeleton(self, kpts):
        """Dibuja el esqueleto del cuerpo detectado"""
        pairs = [(5,7), (7,9), (6,8), (8,10), (5,6), (5,11), (6,12), (11,12)]
        
        for s, e in pairs:
            if kpts[s][0] != 0 and kpts[e][0] != 0:
                s_pos = (int(kpts[s][0]), int(kpts[s][1]))
                e_pos = (int(kpts[e][0]), int(kpts[e][1]))
                pygame.draw.line(self.screen, COLOR_ACCENT, s_pos, e_pos, 4)
        
        for p in kpts:
            if p[0] != 0:
                pygame.draw.circle(self.screen, COLOR_WHITE, (int(p[0]), int(p[1])), 5)

    def draw_ui(self, current_poses):
        """Dibuja la interfaz de usuario"""
        # Panel superior
        panel_height = 80
        pygame.draw.rect(self.screen, (0, 0, 0, 200), (0, 0, WINDOW_WIDTH, panel_height))
        
        # Score
        score_txt = self.font.render(f"SCORE: {self.score}", True, COLOR_WHITE)
        self.screen.blit(score_txt, (20, 15))
        
        # Combo
        combo_color = COLOR_GOLD if self.combo > 5 else COLOR_WHITE
        combo_txt = self.font.render(f"COMBO: x{self.combo}", True, combo_color)
        self.screen.blit(combo_txt, (WINDOW_WIDTH - 250, 15))
        
        # Multiplicador
        if self.multiplier > 1:
            mult_txt = self.small_font.render(f"Multiplicador: x{self.multiplier}", True, COLOR_GOLD)
            self.screen.blit(mult_txt, (WINDOW_WIDTH - 250, 50))
        
        # Instrucciones
        instr = self.small_font.render("Haz la pose cuando toque la LINEA AMARILLA", True, COLOR_TEXT_DIM)
        self.screen.blit(instr, (WINDOW_WIDTH//2 - instr.get_width()//2, 20))
        
        # Mostrar poses activas detectadas (para debug/feedback)
        if current_poses:
            poses_text = ", ".join([self.pose_names[p] for p in current_poses])
            detected_txt = self.small_font.render(f"Detectado: {poses_text}", True, COLOR_ACCENT)
            self.screen.blit(detected_txt, (20, panel_height + 10))
        
        # Estadisticas en esquina inferior derecha
        stats_font = pygame.font.SysFont("Arial", 20)
        accuracy = (self.hits / (self.hits + self.misses) * 100) if (self.hits + self.misses) > 0 else 0
        stats_txt = stats_font.render(f"Precision: {accuracy:.1f}% | Max Combo: {self.max_combo}", True, COLOR_TEXT_DIM)
        self.screen.blit(stats_txt, (WINDOW_WIDTH - 400, WINDOW_HEIGHT - 30))

# ==========================================
# 4. MENU PRINCIPAL
# ==========================================
class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("Arial", 100, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 28)
        self.btn_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.info_font = pygame.font.SysFont("Arial", 18)
        
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        
        # Animaciones
        self.time = 0
        self.particles = self.create_particles()
        
        # Botones estilizados con iconos
        self.buttons = [
            {
                "text": "COMENZAR JUEGO",
                "rect": pygame.Rect(cx - 250, cy + 20, 500, 80),
                "action": "lvl1",
                "color": COLOR_ACCENT,
                "icon": ">"
            },
            {
                "text": "SALIR",
                "rect": pygame.Rect(cx - 250, cy + 130, 500, 80),
                "action": "quit",
                "color": COLOR_DANGER,
                "icon": "X"
            }
        ]
        
        # Informacion de caracteristicas
        self.features = [
            "Deteccion de Poses en Tiempo Real",
            "Sistema de Combos y Multiplicadores",
            "Estadisticas de Rendimiento",
            "Interfaz Cyberpunk Moderna"
        ]

    def create_particles(self):
        """Crea particulas de fondo animadas"""
        particles = []
        for _ in range(30):
            particles.append({
                "x": random.randint(0, WINDOW_WIDTH),
                "y": random.randint(0, WINDOW_HEIGHT),
                "speed": random.uniform(0.2, 1.0),
                "size": random.randint(1, 3),
                "alpha": random.randint(50, 150)
            })
        return particles

    def draw_animated_background(self):
        """Dibuja fondo animado con particulas y grid"""
        # Fondo base
        self.screen.fill(COLOR_BG)
        
        # Grid animado con perspectiva
        grid_offset = int(self.time * 2) % 50
        for i in range(-grid_offset, WINDOW_WIDTH, 50):
            alpha = 40 + int(20 * math.sin(self.time * 0.02 + i * 0.01))
            color = (30, 40, 60 + alpha)
            pygame.draw.line(self.screen, color, (i, 0), (i, WINDOW_HEIGHT), 1)
        
        for i in range(-grid_offset, WINDOW_HEIGHT, 50):
            alpha = 40 + int(20 * math.sin(self.time * 0.02 + i * 0.01))
            color = (30, 40, 60 + alpha)
            pygame.draw.line(self.screen, color, (0, i), (WINDOW_WIDTH, i), 1)
        
        # Particulas flotantes
        for p in self.particles:
            p["y"] -= p["speed"]
            if p["y"] < -10:
                p["y"] = WINDOW_HEIGHT + 10
                p["x"] = random.randint(0, WINDOW_WIDTH)
            
            # Efecto de pulso
            pulse = int(p["alpha"] * (0.7 + 0.3 * math.sin(self.time * 0.05 + p["x"])))
            color = (67, 97, 238, pulse)  # Azul neon con transparencia
            
            pygame.draw.circle(self.screen, color[:3], (int(p["x"]), int(p["y"])), p["size"])
        
        # Lineas decorativas diagonales
        for i in range(5):
            start_x = -200 + int(self.time * (1 + i * 0.3)) % (WINDOW_WIDTH + 400)
            pygame.draw.line(self.screen, (67, 97, 238, 30), 
                           (start_x, 0), (start_x - 300, WINDOW_HEIGHT), 1)

    def draw_title_section(self):
        """Dibuja el titulo con efectos especiales"""
        title_text = "NEURO RHYTHM"
        
        # Efecto de glitch en el titulo
        glitch_offset = int(3 * math.sin(self.time * 0.3)) if random.random() > 0.95 else 0
        
        # Sombra con blur simulado
        for offset in range(5, 0, -1):
            shadow_alpha = 50 - offset * 10
            shadow = self.title_font.render(title_text, True, (0, 0, 0))
            shadow.set_alpha(shadow_alpha)
            self.screen.blit(shadow, (WINDOW_WIDTH//2 - shadow.get_width()//2 + offset, 50 + offset))
        
        # Titulo principal con efecto de brillo
        glow_intensity = int(30 * (1 + math.sin(self.time * 0.1)))
        title_color = (
            min(255, COLOR_ACCENT[0] + glow_intensity),
            min(255, COLOR_ACCENT[1]),
            min(255, COLOR_ACCENT[2] + glow_intensity)
        )
        
        title = self.title_font.render(title_text, True, title_color)
        title_x = WINDOW_WIDTH//2 - title.get_width()//2 + glitch_offset
        self.screen.blit(title, (title_x, 50))
        
        # Linea decorativa debajo del titulo
        line_y = 170
        line_width = 400
        line_x = WINDOW_WIDTH//2 - line_width//2
        
        # Linea principal
        pygame.draw.line(self.screen, COLOR_ACCENT, 
                        (line_x, line_y), (line_x + line_width, line_y), 3)
        
        # Puntos decorativos en los extremos
        for x in [line_x, line_x + line_width]:
            pygame.draw.circle(self.screen, COLOR_ACCENT, (x, line_y), 5)
            pygame.draw.circle(self.screen, COLOR_WHITE, (x, line_y), 2)
        
        # Subtitulo con efecto de escritura
        subtitle = "Arquitectura de Computadores - Proyecto Final"
        sub_surf = self.subtitle_font.render(subtitle, True, COLOR_TEXT_DIM)
        self.screen.blit(sub_surf, (WINDOW_WIDTH//2 - sub_surf.get_width()//2, 190))
        
        # Badge "YOLO v8 + OpenCV"
        badge_text = "POWERED BY YOLO v8"
        badge_surf = self.info_font.render(badge_text, True, COLOR_SECONDARY)
        badge_rect = badge_surf.get_rect(center=(WINDOW_WIDTH//2, 230))
        
        # Fondo del badge
        badge_bg = pygame.Rect(badge_rect.x - 10, badge_rect.y - 5, 
                               badge_rect.width + 20, badge_rect.height + 10)
        pygame.draw.rect(self.screen, (67, 97, 238, 30), badge_bg, border_radius=5)
        pygame.draw.rect(self.screen, COLOR_SECONDARY, badge_bg, 2, border_radius=5)
        
        self.screen.blit(badge_surf, badge_rect)

    def draw_feature_cards(self):
        """Dibuja cards de caracteristicas"""
        start_y = WINDOW_HEIGHT - 200
        card_width = 280
        card_height = 60
        spacing = 20
        total_width = len(self.features) * card_width + (len(self.features) - 1) * spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        
        for i, feature in enumerate(self.features):
            x = start_x + i * (card_width + spacing)
            
            # Fondo de la card con efecto de elevacion
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

# ==========================================
# 5. GESTOR PRINCIPAL
# ==========================================
class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("NEURO RHYTHM - Proyecto Final")
        self.clock = pygame.time.Clock()
        
        print("\n" + "="*50)
        print("NEURO RHYTHM - Sistema Iniciando...")
        print("="*50)
        
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
        if hasattr(self, 'cam'):
            self.cam.release()
        pygame.quit()
        print("Limpieza completada. Hasta pronto!")
        sys.exit(0)

if __name__ == "__main__":
    GameManager().run()
