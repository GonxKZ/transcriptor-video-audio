# Transcriptor de Video/Audio

Una aplicación nativa para Windows hecha con Python 3.13 y PyQt6 que transcribe vídeos o audios de cualquier tamaño con máxima fidelidad, procesando localmente sin costes de licencia.

## Características Principales

- Transcripción local con Whisper Large v3 (faster-whisper + CTranslate2)
- Alineación palabra a palabra con WhisperX
- Diarización opcional con pyannote.audio
- Preprocesamiento de audio con FFmpeg (normalización EBU R128)
- Supresor de ruido opcional con RNNoise
- Interfaz moderna PyQt6 con tours guiados
- Editor de subtítulos con sincronización milimétrica
- Exportación a SRT, VTT, JSON, TSV
- Backend dual: CUDA y ONNX Runtime con DirectML
- Empaquetado con PyInstaller para Windows

## Stack Técnico

- **Reconocimiento de voz**: faster-whisper (CTranslate2) + WhisperX + pyannote.audio
- **Preprocesamiento**: FFmpeg + RNNoise
- **Interfaz**: PyQt6 (Fluent/WinUI)
- **Empaquetado**: PyInstaller + Inno Setup
- **Pruebas**: pytest + pytest-qt + JiWER
- **CI/CD**: GitHub Actions

## Requisitos

- Python 3.13
- FFmpeg en el PATH
- GPU NVIDIA compatible con CUDA (opcional pero recomendado)
- Windows 10/11 para DirectML (opcional)

## Instalación

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -e .

# Para desarrollo
pip install -e .[dev]
```

## Uso

```bash
python -m transcriptor
```

## Desarrollo

```bash
# Linting
ruff check .

# Pruebas
pytest

# Empaquetado
pyinstaller transcriptor.spec
```