# TODO: Plan de Desarrollo del Transcriptor

## Fase 1: Núcleo de Transcripción y UI Básica

-   [ ] **Configuración del Entorno y Dependencias**
    -   [X] Inicializar repositorio Git.
    -   [X] Estructurar proyecto (src, tests).
    -   [X] Definir dependencias en `pyproject.toml`.
    -   [X] Crear y gestionar entorno virtual.
    -   [X] Generar `requirements.txt`.
-   [ ] **Módulo de Pre-procesamiento de Audio (FFmpeg)**
    -   [ ] Implementar extracción de audio desde archivos de video/audio.
    -   [ ] Convertir a PCM mono 16 kHz.
    -   [ ] Aplicar normalización de sonoridad (EBU R128 loudnorm).
    -   [ ] Integrar supresor de ruido opcional (RNNoise).
-   [ ] **Módulo de Segmentación (VAD)**
    -   [ ] Integrar `Silero VAD` para detectar actividad de voz.
    -   [ ] Implementar la división del audio en segmentos de voz.
-   [ ] **Módulo de Transcripción (Whisper)**
    -   [ ] Integrar `faster-whisper` (CTranslate2) para la transcripción.
    -   [ ] Implementar la selección de modelo (tiny, base, small, medium, large-v3).
    -   [ ] Gestionar descarga y cacheo de modelos.
-   [ ] **Interfaz de Usuario Básica (PyQt6)**
    -   [X] Crear ventana principal.
    -   [ ] Diseñar layout: Área de Proyecto, Panel de Proceso, Editor de Transcripción.
    -   [ ] Implementar menú para importar archivos.
    -   [ ] Mostrar forma de onda del audio.
    -   [ ] Añadir controles para iniciar/pausar el proceso.

## Fase 2: Funcionalidad Avanzada y UX

-   [ ] **Alineación y Diarización**
    -   [ ] Integrar `WhisperX` para alineación a nivel de palabra.
    -   [ ] Integrar `pyannote.audio` para diarización (identificación de hablantes).
    -   [ ] Gestionar token de Hugging Face para `pyannote`.
-   [ ] **Editor de Transcripción Avanzado**
    -   [ ] Mostrar transcripción con timestamps por palabra.
    -   [ ] Sincronizar reproducción de audio con el texto.
    -   [ ] Permitir la edición de texto (WYSIWYG).
    -   [ ] Permitir el ajuste de tiempos de los segmentos/palabras.
    -   [ ] Colorear segmentos por hablante (diarización).
-   [ ] **Mejoras de UX**
    -   [ ] Implementar tours guiados ("coach marks").
    -   [ ] Añadir ayuda contextual ("What's This?").
    -   [ ] Crear perfiles de configuración predefinidos (Rápido, Equilibrado, Fidelidad).
    -   [ ] Implementar tema oscuro/claro automático.
-   [ ] **Exportación de Resultados**
    -   [ ] Generar archivos de subtítulos (SRT, VTT).
    -   [ ] Exportar transcripción en formato JSON y TXT.

## Fase 3: Robustez, Pruebas y Distribución

-   [ ] **Arquitectura de Procesamiento Robusta**
    -   [ ] Implementar pipeline por streaming con colas.
    -   [ ] Asegurar tolerancia a fallos (guardar estado y reanudar).
    -   [ ] Gestionar workers para CPU y GPU.
-   [ ] **Pruebas y Calidad de Código**
    -   [ ] Configurar `ruff` para linting.
    -   [ ] Integrar `JiWER` para medir precisión (WER).
    -   [ ] Escribir tests unitarios y de integración con `pytest`.
    -   [ ] Escribir tests de UI con `pytest-qt`.
-   [ ] **Backend Alternativo (ONNX)**
    -   [ ] Investigar exportación de modelos a ONNX.
    -   [ ] Implementar backend opcional con ONNX Runtime y DirectML (para Windows).
-   [ ] **Empaquetado y Distribución**
    -   [ ] Configurar `PyInstaller` o `Nuitka` para crear el ejecutable.
    -   [ ] Crear un instalador para Windows (Inno Setup).
    -   [ ] Configurar CI/CD con GitHub Actions.
