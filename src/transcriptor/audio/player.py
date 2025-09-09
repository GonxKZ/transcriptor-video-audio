"""
Audio playback engine using QMediaPlayer.
"""
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioPlayer(QObject):
    """Wraps QMediaPlayer for audio playback control."""
    
    position_changed = pyqtSignal(int)  # Emits position in milliseconds
    duration_changed = pyqtSignal(int)  # Emits duration in milliseconds
    state_changed = pyqtSignal(QMediaPlayer.PlaybackState)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        
        # Connect signals
        self._player.positionChanged.connect(self.position_changed.emit)
        self._player.durationChanged.connect(self.duration_changed.emit)
        self._player.playbackStateChanged.connect(self.state_changed.emit)

    def load(self, file_path: str):
        """Load an audio file for playback."""
        self._player.setSource(QUrl.fromLocalFile(file_path))

    def play(self):
        """Start or resume playback."""
        self._player.play()

    def pause(self):
        """Pause playback."""
        self._player.pause()

    def stop(self):
        """Stop playback and reset position."""
        self._player.stop()

    def seek(self, position_ms: int):
        """Seek to a specific position in the audio."""
        self._player.setPosition(position_ms)

    @property
    def state(self) -> QMediaPlayer.PlaybackState:
        return self._player.playbackState()

    @property
    def duration(self) -> int:
        return self._player.duration()
