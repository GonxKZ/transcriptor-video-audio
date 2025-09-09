"""
Waveform display widget using pyqtgraph for efficient audio visualization.
"""
import numpy as np
import soundfile as sf
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
import pyqtgraph as pg

class WaveformWidget(QWidget):
    """A widget to display and interact with an audio waveform."""
    
    position_clicked = pyqtSignal(float)  # Emits position in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup pyqtgraph config
        pg.setConfigOptions(antialias=True)
        
        self.waveform_plot = pg.PlotWidget()
        self.waveform_item = self.waveform_plot.getPlotItem()
        self.waveform_item.setMouseEnabled(x=True, y=False)
        self.waveform_item.setLimits(yMin=-1, yMax=1)
        self.waveform_item.hideAxis('left')
        self.waveform_item.showAxis('bottom')
        
        # Add infinite line for cursor
        self.cursor = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('r', width=2))
        self.waveform_plot.addItem(self.cursor, ignoreBounds=True)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.waveform_plot)
        
        # Connect signals
        self.waveform_item.scene().sigMouseClicked.connect(self.on_mouse_clicked)
        
        self.audio_data = None
        self.sample_rate = None

    def load_audio(self, file_path: str):
        """Load audio data from a file."""
        try:
            self.audio_data, self.sample_rate = sf.read(file_path)
            # Normalize to -1, 1
            if self.audio_data.max() > 1.0:
                self.audio_data = self.audio_data / np.iinfo(self.audio_data.dtype).max
            
            duration_seconds = len(self.audio_data) / self.sample_rate
            time_axis = np.linspace(0, duration_seconds, num=len(self.audio_data))
            
            self.waveform_plot.plot(time_axis, self.audio_data, pen=pg.mkPen('c', width=1.5))
            self.waveform_item.setXRange(0, duration_seconds)
            self.cursor.setPos(0)
            
        except Exception as e:
            print(f"Error loading waveform: {e}")

    def set_cursor_position(self, position_seconds: float):
        """Set the cursor position on the waveform."""
        self.cursor.setPos(position_seconds)

    def on_mouse_clicked(self, event):
        """Handle mouse clicks on the plot."""
        if event.double():
            return # Ignore double clicks
            
        pos = event.scenePos()
        if self.waveform_item.sceneBoundingRect().contains(pos):
            mouse_point = self.waveform_item.vb.mapSceneToView(pos)
            self.position_clicked.emit(mouse_point.x())
