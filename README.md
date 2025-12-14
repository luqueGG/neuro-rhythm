# Proyecto: Neuro Rhythm

**UNIVERSIDAD NACIONAL SAN AGUSTÍN DE AREQUIPA**

**ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS**

![][image1]

**ARQUITECTURA DE COMPUTADORES**

**Neuro Rhythm**

**Docente:** Pedro Alex Rodriguez Gonzales

**Integrantes:**

- Morocco Saico, Jose Manuel  
- Luque Guevara Fernando Gerson

**Grupo:** A

                                               **Arequipa \- 2025**

**1\. Introducción**  
El presente proyecto, titulado “Neuro Rhythm: Interfaz Natural de Usuario (NUI) basada en Visión Artificial para la Gamificación del Ejercicio”, consiste en el desarrollo de un sistema informático interactivo que integra componentes de hardware y software con el objetivo de interconectar el mundo físico del usuario con un entorno digital en tiempo real.  
El sistema se implementa como una aplicación de escritorio que utiliza una cámara web convencional como único dispositivo de entrada. A partir de la captura continua de video, el software procesa las imágenes mediante técnicas de visión artificial e inteligencia artificial, específicamente redes neuronales convolucionales entrenadas para la estimación de la postura humana. Como resultado, se obtiene un conjunto de puntos clave (keypoints) que representan el esqueleto digital del usuario.  
Estas coordenadas corporales son interpretadas por la lógica del sistema para permitir la interacción directa con una interfaz gráfica tipo videojuego de ritmo, sin necesidad de dispositivos físicos adicionales como mouse, teclado o controles dedicados. De esta manera, los movimientos corporales del usuario se transforman en comandos de entrada que influyen en la dinámica del juego.  
En conjunto, Neuro Rhythm plantea una alternativa de bajo costo para el acceso a experiencias de exergaming, demostrando que es posible replicar funcionalidades presentes en sistemas comerciales mediante el uso eficiente de software, hardware común y herramientas de código abierto.  
 	  
**2\. Problemática**  
La interacción tradicional entre el usuario y los sistemas informáticos se basa principalmente en dispositivos de entrada manuales como el teclado y el mouse, los cuales promueven un uso prolongado en posiciones estáticas. Estudios en el ámbito de la salud digital, así como directrices de la Organización Mundial de la Salud (OMS), señalan que este tipo de interacción favorece el sedentarismo tecnológico, asociado a una reducción de la actividad física y a riesgos para la salud a mediano y largo plazo \[1\].

Como respuesta a esta problemática, en los últimos años han surgido propuestas basadas en exergaming y *serious games*, las cuales integran el movimiento corporal como parte de la interacción digital, incrementando la motivación y la participación del usuario \[2\], \[3\]. No obstante, la mayoría de estas soluciones se apoyan en hardware propietario y de alto costo, como consolas con sensores dedicados o sistemas de realidad virtual, lo que restringe su acceso en contextos educativos y domésticos.

En consecuencia, existe la necesidad de desarrollar interfaces que fomenten la actividad física utilizando hardware ampliamente disponible, manteniendo un rendimiento adecuado para aplicaciones en tiempo real. La problemática abordada por este proyecto se centra en cómo transformar el movimiento corporal en un mecanismo de interacción digital accesible, sin depender de dispositivos especializados.

Frente a este escenario, Neuro Rhythm propone una alternativa de bajo costo que emplea visión artificial para convertir la cámara web en un sensor de movimiento, reduciendo barreras económicas y técnicas, y ofreciendo una base abierta para el análisis y desarrollo académico.

**3\. Trabajos Relacionados**  
Para el desarrollo de la presente interfaz se realizó una revisión bibliográfica centrada en la evolución de la captura de movimiento humano y su aplicación en interfaces interactivas, considerando desde soluciones basadas en hardware dedicado hasta enfoques modernos sustentados en visión artificial y aprendizaje profundo.

### ***3.1 Estimación de postura basada en visión artificial***

Uno de los referentes iniciales en este ámbito es el trabajo de Shotton et al. \[4\], desarrollado en Microsoft Research, donde se propone un método de reconocimiento de la postura humana en tiempo real utilizando imágenes de profundidad capturadas por el sensor Kinect. Este sistema representó un avance significativo al permitir la interacción sin controles físicos; sin embargo, su dependencia de sensores RGB-D e infraestructura especializada incrementa los costos y limita su portabilidad. Dicho trabajo establece un estándar de precisión relevante para este proyecto, aunque con un enfoque distinto al sustituir el hardware dedicado por procesamiento puramente software.

### ***3.2 Estimación de postura basada en visión artificial***

Con la consolidación de las redes neuronales convolucionales, Cao et al. \[5\] introdujeron OpenPose, un sistema capaz de realizar estimación de postura 2D de múltiples personas en tiempo real a partir de imágenes RGB, mediante el uso de *Part Affinity Fields*. Este estudio demostró la viabilidad de extraer esqueletos digitales sin sensores de profundidad, aunque a costa de un elevado requerimiento computacional, generalmente asociado al uso de GPU.

### ***3.3 Arquitecturas optimizadas para tiempo real***

Con el objetivo de optimizar el rendimiento en aplicaciones interactivas, Redmon et al. \[6\] presentaron la arquitectura YOLO (*You Only Look Once*), orientada a maximizar la velocidad de inferencia mediante un enfoque de detección en una sola etapa. Si bien inicialmente fue diseñada para detección de objetos, su filosofía de eficiencia y baja latencia resulta especialmente adecuada para sistemas que requieren respuesta en tiempo real.

### ***3.4 Extensión de YOLO para estimación de postura***

La aplicación de la arquitectura YOLO a la estimación de postura fue formalizada por Maji et al. \[7\] mediante la propuesta YOLO-Pose, un método *heatmap-free* capaz de detectar simultáneamente personas y sus puntos clave articulares en una única pasada de la red neuronal. Este enfoque logra un equilibrio entre precisión y eficiencia computacional, permitiendo su ejecución en hardware convencional. En conjunto, estos trabajos constituyen la base conceptual y técnica de Neuro Rhythm, al demostrar que es posible implementar interfaces corporales interactivas de bajo costo y baja latencia utilizando únicamente cámaras RGB y modelos optimizados de visión artificial.

**4\. Herramientas: Software, Librerías y Periféricos Utilizados**  
Para el desarrollo del proyecto Neuro Rhythm se emplearon herramientas de hardware y software seleccionadas en función de su disponibilidad, compatibilidad y adecuación para aplicaciones interactivas en tiempo real. La elección de estas tecnologías permite garantizar la viabilidad del sistema en entornos domésticos y académicos, sin requerir infraestructura especializada.  
***4.1 Hardware***

El sistema fue diseñado para ejecutarse en una computadora personal o laptop convencional, sin necesidad de aceleradores gráficos dedicados. Como dispositivo principal de entrada se utilizó una cámara web genérica, integrada o externa, con una resolución mínima de 640×480 píxeles. Este dispositivo cumple la función de sensor visual, permitiendo la captura continua del movimiento corporal del usuario.

Para un funcionamiento adecuado, se recomienda un equipo con procesador de gama media (Intel Core i5 o equivalente), capaz de manejar la inferencia del modelo de visión artificial y el renderizado gráfico de manera simultánea. La salida del sistema se realiza a través de la pantalla del equipo, donde se muestran tanto el video capturado como la interfaz gráfica interactiva del juego.

***4.2 Software***

El desarrollo de la aplicación se realizó utilizando el lenguaje de programación Python, debido a su amplio ecosistema de librerías orientadas a visión artificial, inteligencia artificial y desarrollo de aplicaciones interactivas. La versión empleada corresponde a Python 3.10 o superior, garantizando compatibilidad con los frameworks utilizados.

El modelo de estimación de postura humana se implementó mediante Ultralytics YOLOv8n-pose, una versión optimizada del modelo YOLO orientada a la detección de puntos clave del cuerpo humano. Este modelo preentrenado permite obtener, en tiempo real, las coordenadas del esqueleto del usuario a partir de imágenes RGB, priorizando la eficiencia computacional.

Para la captura y preprocesamiento de video se utilizó la librería OpenCV (cv2), encargada de acceder a la cámara web, manejar el flujo de imágenes y realizar operaciones básicas como el espejado y la conversión de espacios de color. Las operaciones matemáticas y el manejo de matrices de datos se apoyaron en NumPy, optimizando el procesamiento de las coordenadas obtenidas.

La construcción de la interfaz gráfica, el manejo del bucle principal del sistema y la gestión de eventos se desarrollaron con Pygame, librería que facilita la creación de aplicaciones interactivas en tiempo real. Pygame se encarga del renderizado de los elementos visuales, la superposición del esqueleto digital y la presentación de información como puntajes y retroalimentación al usuario.

***4.3 Librerías y dependencias***

Las principales librerías utilizadas en el proyecto son:

* Ultralytics (YOLOv8): estimación de postura humana en tiempo real.  
* OpenCV: captura y procesamiento de imágenes.  
* Pygame: interfaz gráfica y lógica del juego.  
* NumPy: operaciones matemáticas y manejo eficiente de datos.

Todas las herramientas empleadas son de código abierto, lo que elimina costos de licenciamiento y facilita la replicabilidad del proyecto.

**5\. Instalación de Hardware y Software**  
El despliegue del proyecto requiere las siguientes configuraciones:

### ***5.1 Instalación de hardware***

El único componente de hardware adicional requerido es una cámara web convencional, integrada o externa, conectada al equipo mediante interfaz USB (Plug & Play). Para un funcionamiento adecuado, se recomienda ubicar la cámara a una distancia aproximada de 1.5 a 2 metros del usuario, permitiendo la captura completa del cuerpo dentro del campo visual.

Asimismo, se sugiere contar con un espacio despejado frente a la cámara, evitando obstáculos que puedan interferir con la detección de la postura corporal. No se requiere ningún tipo de calibración manual del hardware.

*![][image2]*  
*Figura 1\. Ubicación recomendada de la cámara web frente al usuario*

### ***5.2 Instalación de software***

El sistema se ejecuta sobre un entorno de desarrollo basado en Python 3.10 o superior. Con el fin de aislar dependencias y garantizar la correcta ejecución del proyecto, se recomienda la creación de un entorno virtual.

Inicialmente, se clona el repositorio del proyecto desde el sistema de control de versiones:

```shell
git clone https://github.com/luqueGG/neuro-rhythm.git
cd neuro-rhythm
```

Posteriormente, se crea y activa un entorno virtual:

```shell
python -m venv venv
source venv/bin/activate # En Linux / macOS
venv\Scripts\activate # En Windows
```

Una vez activado el entorno virtual, se instalan las dependencias del proyecto utilizando el archivo de requisitos:

```shell
pip install -r requirements.txt
```

Las principales librerías incluidas corresponden a:

* Ultralytics (YOLOv8) para estimación de postura humana.  
* OpenCV para la captura y procesamiento de video.  
* Pygame para la interfaz gráfica y la lógica interactiva.  
* NumPy para el manejo eficiente de datos y operaciones matemáticas.

Durante la primera ejecución del sistema, los pesos del modelo preentrenado YOLOv8n-pose se descargan automáticamente, por lo que no se requiere una configuración manual adicional.

### ***5.3 Ejecución del sistema***

Una vez completada la instalación de las dependencias, el sistema se inicia ejecutando el archivo principal del proyecto:

```shell
python main.py
```

Al iniciarse, la aplicación verifica el acceso a la cámara web, carga el modelo de visión artificial y muestra el menú principal del sistema, desde el cual el usuario puede comenzar la interacción.

**6\. Propuesta de Solución General**  
La solución propuesta en el proyecto Neuro Rhythm se fundamenta en una arquitectura modular que integra visión artificial, procesamiento lógico y renderizado gráfico en tiempo real. El objetivo principal es transformar los movimientos corporales del usuario en comandos de interacción dentro de un entorno digital gamificado, utilizando únicamente una cámara web convencional como dispositivo de entrada.

### ***6.1 Visión general del sistema***

El sistema sigue un flujo continuo de procesamiento basado en el esquema Entrada – Proceso – Salida, el cual permite comprender de manera clara la interacción entre los distintos componentes del proyecto.

*![][image3]*  
*Figura 2\. Esquemático general del sistema: Entrada, Proceso y Salida*

En la Figura 2, se identifican tres bloques principales:

* **Entrada:** Captura de video en tiempo real mediante la cámara web.  
* **Proceso:** Análisis de las imágenes utilizando herramientas para detección de la postura corporal.  
* **Salida:** Representación gráfica interactiva que responde a los movimientos del usuario.

### ***6.2 Entrada: Captura de movimiento***

La etapa de entrada consiste en la adquisición continua de frames de video desde la cámara web. Cada imagen capturada representa el estado instantáneo de la postura del usuario frente al sistema. Este flujo de datos visuales constituye la materia prima para el procesamiento posterior, sin requerir sensores adicionales ni dispositivos especializados.

Antes de ser analizados por el modelo de inteligencia artificial, los frames pueden ser sometidos a operaciones básicas de preprocesamiento, como el espejado horizontal, con el fin de mejorar la percepción de correspondencia entre el movimiento real y su representación en pantalla.

### ***6.3 Proceso: Análisis y lógica del sistema***

En la etapa de procesamiento, cada frame es analizado por el modelo de estimación de postura humana basado en YOLOv8-pose. El modelo identifica al usuario dentro de la imagen y extrae un conjunto de puntos clave (keypoints) que representan las principales articulaciones del cuerpo humano.

Las coordenadas obtenidas son evaluadas por la lógica del sistema para determinar si el usuario está ejecutando determinadas posturas o movimientos predefinidos. Esta lógica se basa en comparaciones espaciales simples entre puntos clave, permitiendo detectar acciones como elevación de brazos o desplazamientos laterales.

Adicionalmente, el sistema gestiona el estado del juego, controlando la generación de objetivos, la validación de colisiones y la actualización del puntaje en función de las acciones detectadas.

### ***6.4 Salida: Interfaz gráfica interactiva***

La etapa de salida corresponde a la representación visual del sistema. A través de la interfaz gráfica, el usuario observa el video capturado con el esqueleto digital superpuesto, así como los elementos propios del videojuego de ritmo, tales como objetivos, indicadores visuales y puntajes.

Esta retroalimentación visual en tiempo real permite al usuario comprender de forma inmediata si sus movimientos están siendo correctamente interpretados por el sistema, cerrando el ciclo de interacción entre el mundo físico y el entorno digital.

**7\. Desarrollo de Software: Código y Documentación**  
En esta sección se presentan los fragmentos más representativos del código desarrollado en el proyecto Neuro Rhythm, con el objetivo de documentar la implementación del sistema y evidenciar la integración entre captura de video, visión artificial, lógica de interacción y renderizado gráfico. Los fragmentos seleccionados ilustran las funciones clave del sistema sin detallar la totalidad del código fuente el cual está en el repositorio.

### ***7.1 Inicialización del sistema***

En la fase inicial se configuran los recursos principales del sistema: el acceso a la cámara web, la carga del modelo de estimación de postura y la inicialización del entorno gráfico.

```py
from ultralytics import YOLO
import cv2
import pygame

model = YOLO("yolov8n-pose.pt")
cap = cv2.VideoCapture(0)

pygame.init()
screen = pygame.display.set_mode((800, 600))
```

Este fragmento muestra cómo el sistema prepara los componentes necesarios para la ejecución en tiempo real, estableciendo la base para la interacción posterior.

### ***7.2 Captura y preprocesamiento de video***

La captura de movimiento se realiza mediante la lectura continua de frames desde la cámara web. Para mejorar la percepción del usuario, se aplica un espejado horizontal a la imagen capturada.

```py
ret, frame = cap.read()
frame = cv2.flip(frame, 1)
```

Cada frame representa el estado instantáneo de la postura del usuario y constituye la entrada principal para el procesamiento mediante visión artificial.

### ***7.3 Detección de postura humana***

El análisis de la postura se lleva a cabo utilizando el modelo YOLOv8-pose, el cual procesa cada frame y devuelve un conjunto de puntos clave que describen las articulaciones del cuerpo humano.

```py
results = model(frame)
keypoints = results[0].keypoints.xy
```

Las coordenadas obtenidas conforman el esqueleto digital del usuario, permitiendo representar su movimiento corporal dentro del entorno virtual.

### ***7.4 Análisis de movimiento y lógica de interacción***

A partir de los puntos clave detectados, el sistema evalúa relaciones espaciales simples para identificar gestos específicos. Este enfoque permite una detección eficiente sin requerir cálculos complejos.

```py
if wrist_y < shoulder_y:
pose_detected = True
```

### ***7.5 Gestión de estados del juego***

El comportamiento del sistema se controla mediante un modelo de estados finitos que separa el menú principal de la fase de juego activo.

```py
if state == "MENU":
draw_menu()
elif state == "GAME":
run_game()
```

Esta estructura permite mantener un flujo de interacción claro y controlado durante la ejecución del sistema.

### ***7.6 Renderizado e interfaz gráfica***

La interfaz gráfica se actualiza continuamente para reflejar los movimientos del usuario y el estado del juego. En esta etapa se integran el video capturado, el esqueleto digital y los elementos visuales del videojuego.

```py
screen.blit(game_surface, (0, 0))
pygame.display.update()
```

La retroalimentación visual en tiempo real refuerza la sensación de interacción natural, cerrando el ciclo entre el movimiento físico y su representación digital.

**8\. Resultados: Interfaces**  
En esta sección se presentan los resultados visuales obtenidos durante la ejecución del sistema Neuro Rhythm, con el fin de evidenciar el correcto funcionamiento de la interfaz natural de usuario y la interacción en tiempo real entre el movimiento corporal del usuario y el entorno digital. Las interfaces mostradas corresponden a las principales etapas de uso del sistema.

### ***8.1 Interfaz de inicio y menú principal***

*![][image4]*  
*Figura 3\. Menú principal del sistema Neuro Rhythm.*

En esta interfaz se muestra la pantalla inicial del sistema, desde la cual el usuario puede iniciar la experiencia interactiva. El diseño del menú es simple e intuitivo, permitiendo una transición clara hacia la fase de juego. Esta pantalla confirma la correcta inicialización del entorno gráfico y la disponibilidad del sistema.

### ***8.2 Captura de video en tiempo real***

*![][image5]*  
*Figura 4\. Visualización del usuario frente a la cámara web.*

La imagen presenta la captura de video en tiempo real obtenida desde la cámara web. Esta interfaz permite verificar que el sistema reconoce correctamente la presencia del usuario y que el encuadre corporal es adecuado para la detección de postura.

### ***8.3 Detección de postura y esqueleto digital***

*![][image6]*  
*Figura 5\. Esqueleto digital superpuesto al cuerpo del usuario.*

En esta interfaz se observa la superposición del esqueleto digital generado por el modelo de visión artificial sobre la imagen del usuario. Los puntos clave y las conexiones entre articulaciones evidencian la correcta estimación de la postura humana utilizando únicamente una cámara RGB convencional.

### ***8.4 Reconocimiento de gestos***

*![][image7]*  
*Figura 6\. Detección de pose corporal durante la ejecución del juego.*

La figura muestra un ejemplo de reconocimiento de un gesto corporal específico, validado mediante indicadores visuales en pantalla. Esta interfaz demuestra que el sistema interpreta correctamente los movimientos del usuario y los traduce en acciones dentro del videojuego.

### ***8.5 Interfaz del juego en ejecución***

*![][image8]*  
*Figura 7\. Juego de ritmo en ejecución con indicadores visuales y puntaje.*

En esta pantalla se visualiza el videojuego en funcionamiento, integrando el video capturado, el esqueleto digital, los objetivos rítmicos y el puntaje del usuario. La interfaz confirma la interacción fluida entre el movimiento físico y la dinámica del juego.

### ***8.6 Desempeño del sistema***

Durante las pruebas realizadas, el sistema logró mantener una tasa de actualización estable, permitiendo una interacción continua sin interrupciones perceptibles. En un equipo de gama media, la aplicación alcanzó un rendimiento aproximado de X cuadros por segundo (FPS), suficiente para aplicaciones de exergaming en tiempo real.

**9\. Viabilidad del Proyecto**  
La viabilidad del proyecto Neuro Rhythm se evalúa considerando tres dimensiones fundamentales: técnica, económica y social, las cuales permiten determinar la factibilidad real de su implementación y uso en un contexto académico y doméstico.

### ***9.1 Viabilidad técnica***

Desde el punto de vista técnico, el proyecto es viable debido al uso de tecnologías consolidadas y herramientas de código abierto ampliamente documentadas. La estimación de postura humana se realiza mediante el modelo YOLOv8n-pose, el cual ha sido diseñado para ofrecer un equilibrio adecuado entre precisión y velocidad de inferencia. Esto permite que el sistema funcione en tiempo real sobre equipos de cómputo personales sin requerir hardware especializado, como tarjetas gráficas dedicadas de alto rendimiento.

Asimismo, la arquitectura del software se apoya en librerías estables como OpenCV para la captura de video y Pygame para la gestión de la interfaz gráfica y la lógica del juego, garantizando compatibilidad multiplataforma. Las pruebas realizadas demuestran que el sistema mantiene una tasa de cuadros por segundo aceptable para aplicaciones interactivas, validando su correcto desempeño.

### ***9.2 Viabilidad económica***

En términos económicos, el proyecto presenta una alta viabilidad, ya que no implica costos adicionales en licencias de software ni en adquisición de hardware propietario. Todas las herramientas empleadas son de libre acceso y distribución abierta. El único requerimiento físico es una cámara web convencional, generalmente integrada en laptops o de bajo costo en el mercado.

Esta característica convierte a Neuro Rhythm en una solución accesible para estudiantes, instituciones educativas y usuarios domésticos, eliminando barreras económicas asociadas a sistemas comerciales de exergaming que dependen de consolas o sensores especializados.

### ***9.3 Viabilidad social***

Desde una perspectiva social, el proyecto es pertinente y viable al promover la actividad física mediante una experiencia interactiva y lúdica. Al transformar el ejercicio en una dinámica de juego, se incentiva la participación activa del usuario y se combate el sedentarismo tecnológico.

Además, la accesibilidad del sistema favorece su posible aplicación en entornos educativos, recreativos o de sensibilización sobre hábitos saludables. El uso de interfaces naturales basadas en movimiento corporal facilita la inclusión de usuarios con distintos niveles de experiencia tecnológica, ampliando su impacto potencial.

**10\. Trabajos Futuros**  
Si bien el proyecto Neuro Rhythm cumple con los objetivos planteados en esta etapa, existen diversas líneas de mejora y ampliación que podrían desarrollarse en trabajos futuros para incrementar su alcance, precisión y valor funcional.

Una primera línea de trabajo corresponde a la incorporación de sincronización musical automática. Mediante el análisis de señales de audio (por ejemplo, utilizando técnicas de Transformada Rápida de Fourier – FFT), sería posible generar los objetivos del juego en función del ritmo y la intensidad de la música, mejorando la coherencia entre movimiento corporal y estímulo sonoro.

Otra mejora potencial es la implementación de mecanismos de calibración automática del usuario. Este proceso permitiría adaptar dinámicamente los umbrales de detección de poses según la estatura, posición y rango de movimiento de cada persona, incrementando la precisión del reconocimiento y reduciendo errores en distintos entornos de uso.

Asimismo, se plantea como trabajo futuro la reincorporación de detección de motricidad fina, mediante algoritmos especializados en reconocimiento de manos y gestos. Esta funcionalidad, descartada en la presente fase para priorizar la estabilidad del reconocimiento corporal completo, permitiría ampliar las interacciones hacia tareas de mayor precisión.

Finalmente, el sistema podría evolucionar hacia un enfoque multijugador o de seguimiento de progreso, incorporando perfiles de usuario, registro de puntajes y métricas de desempeño físico, lo que abriría posibilidades de aplicación en contextos educativos, recreativos o de entrenamiento físico supervisado.

**11\. Conclusiones**

El desarrollo del proyecto Neuro Rhythm permitió aplicar de forma integrada los conceptos de interacción entre hardware y software, demostrando cómo los movimientos corporales del usuario pueden ser capturados, procesados y convertidos en acciones dentro de un entorno digital en tiempo real.

A través de la implementación de técnicas de visión artificial y aprendizaje profundo, se evidenció que el uso del modelo YOLOv8n-pose ofrece un equilibrio adecuado entre precisión y velocidad, siendo viable para aplicaciones interactivas sin necesidad de hardware especializado. Esta experiencia reforzó la comprensión del impacto que tienen las capacidades del hardware sobre el desempeño del software.

Asimismo, el proyecto permitió afianzar conocimientos fundamentales de la Arquitectura de Computadores al analizar el flujo de datos desde los dispositivos de entrada, pasando por el procesamiento computacional, hasta su representación visual como salida.

Finalmente, Neuro Rhythm demuestra que es posible desarrollar interfaces naturales de usuario accesibles y de bajo costo, capaces de fomentar la actividad física mediante la gamificación. Los resultados obtenidos validan el cumplimiento de los objetivos propuestos y establecen una base sólida para futuras extensiones del sistema.

## **12\. Referencias**

\[1\] World Health Organization, “Directrices de la OMS Sobre Actividad Física y Comportamientos Sedentarios,” *NCBI Bookshelf*, 2021\. [https://www.ncbi.nlm.nih.gov/books/NBK581972/](https://www.ncbi.nlm.nih.gov/books/NBK581972/)   
   
\[2\] M. Zyda, “From visual simulation to virtual reality to games,” *Computer*, vol. 38, no. 9, pp. 25–32, Sep. 2005, doi: 10.1109/mc.2005.297. 

\[3\] Oh Y, Yang S, editors. Defining exergames & exergaming. Meaningful play 2010 conference 2010 october 21 \- 23\. East Lansing: Michigan State University, MI, USA: MSU Serious Games Program; 2010\.

\[4\] J. Shotton et al., "Real-time human pose recognition in parts from single depth images," CVPR 2011, Colorado Springs, CO, USA, 2011, pp. 1297-1304, doi: 10.1109/CVPR.2011.5995316. 

\[5\] Z. Cao, T. Simon, S.-E. Wei, and Y. Sheikh, “Realtime Multi-Person 2D Pose Estimation using Part Affinity Fields,” in 2017 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Honolulu, HI, Jul. 2017, pp. 1302–1310. doi: 10.1109/CVPR.2017.143

\[6\] J. Redmon, S. Divvala, R. Girshick and A. Farhadi, "You Only Look Once: Unified, Real-Time Object Detection," 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Las Vegas, NV, USA, 2016, pp. 779-788, doi: 10.1109/CVPR.2016.91.

\[7\] D. Maji, S. Nagori, M. Mathew, and D. Poddar, “YOLO-Pose: Enhancing YOLO for multi person pose estimation using object Keypoint similarity loss,” *arXiv (Cornell University)*, Apr. 2022, doi: 10.48550/arxiv.2204.06806.

