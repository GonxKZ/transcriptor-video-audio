"""
Main window for the Transcriptor application with modern Fluent/WinUI design.
"""
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QLabel, QPushButton, QFileDialog, QProgressBar, QToolBar,
    QStatusBar, QSizePolicy, QMenuBar, QMenu, QMessageBox, QApplication
)
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from ..audio.preprocessor import AudioPreprocessor
from ..utils.config import ConfigManager
from .tour import TourManager, ContextualHelp
from .editor import TranscriptionEditor, Segment, Word
from .fluent_design import FluentDesignSystem
from .windows_effects import WindowsFluentEffects
from ..audio.player import AudioPlayer
from ..pipeline.streaming import StreamingPipeline, ProcessingState, ProcessingStage
from .waveform_widget import WaveformWidget
from .settings_dialog import SettingsDialog

class ThemeManager:
    """Manages application themes (light/dark/auto) using Fluent Design System."""
    
    @staticmethod
    def apply_theme(app, theme="auto"):
        """Apply the specified theme to the application."""
        if theme == "dark" or (theme == "auto" and ThemeManager._is_system_dark()):
            ThemeManager._apply_fluent_theme(app, "dark")
        else:
            ThemeManager._apply_fluent_theme(app, "light")
    
    @staticmethod
    def _is_system_dark():
        """Check if the system is using a dark theme."""
        # Simple check - in a real app, you'd want to check the OS setting
        palette = QApplication.palette()
        return palette.color(QPalette.ColorRole.Window).lightness() < 128
    
    @staticmethod
    def _apply_fluent_theme(app, theme_name):
        """Apply a Fluent Design theme to the application."""
        colors = FluentDesignSystem.get_theme_colors(theme_name)
        
        # Create palette
        palette = QPalette()
        
        # Set up the palette with Fluent colors
        palette.setColor(QPalette.ColorRole.Window, colors["background"])
        palette.setColor(QPalette.ColorRole.WindowText, colors["on_surface"])
        palette.setColor(QPalette.ColorRole.Base, colors["surface"])
        palette.setColor(QPalette.ColorRole.AlternateBase, colors["surface_variant"])
        palette.setColor(QPalette.ColorRole.ToolTipBase, colors["on_surface"])
        palette.setColor(QPalette.ColorRole.ToolTipText, colors["on_surface"])
        palette.setColor(QPalette.ColorRole.Text, colors["on_surface"])
        palette.setColor(QPalette.ColorRole.Button, colors["surface"])
        palette.setColor(QPalette.ColorRole.ButtonText, colors["on_surface"])
        palette.setColor(QPalette.ColorRole.BrightText, colors["error"])
        palette.setColor(QPalette.ColorRole.Link, colors["primary"])
        palette.setColor(QPalette.ColorRole.Highlight, colors["primary"])
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        
        # Apply Fluent Design styles
        app.setStyleSheet(ThemeManager._get_fluent_stylesheet(theme_name))
    
    @staticmethod
    def _get_fluent_stylesheet(theme_name):
        """Get the Fluent Design stylesheet for the specified theme."""
        colors = FluentDesignSystem.get_theme_colors(theme_name)
        spacing_md = FluentDesignSystem.get_spacing("md")
        spacing_lg = FluentDesignSystem.get_spacing("lg")
        border_radius = FluentDesignSystem.get_border_radius("md")
        
        return f"""
            /* Global styles */
            QMainWindow {{
                background-color: {colors['background'].name()};
                font-family: "Segoe UI", sans-serif;
            }}
            
            /* Tooltips */
            QToolTip {{
                color: {colors['on_surface'].name()};
                background-color: {colors['surface'].name()};
                border: 1px solid {colors['outline'].name()};
                border-radius: {border_radius}px;
                padding: {spacing_md}px;
                font-size: 12px;
            }}
            
            /* Menu bar */
            QMenuBar {{
                background-color: {colors['surface'].name()};
                padding: 0;
                border: none;
            }}
            
            QMenuBar::item {{
                background: transparent;
                padding: {spacing_md}px {spacing_lg}px;
                color: {colors['on_surface'].name()};
            }}
            
            QMenuBar::item:selected {{
                background: {colors['secondary'].name()};
            }}
            
            QMenuBar::item:pressed {{
                background: {colors['primary'].name()};
                color: white;
            }}
            
            /* Menus */
            QMenu {{
                background-color: {colors['surface'].name()};
                border: 1px solid {colors['outline'].name()};
                border-radius: {border_radius}px;
                padding: {spacing_md}px 0;
            }}
            
            QMenu::item {{
                padding: {spacing_md}px {spacing_lg}px;
                color: {colors['on_surface'].name()};
            }}
            
            QMenu::item:selected {{
                background-color: {colors['secondary'].name()};
            }}
            
            QMenu::item:disabled {{
                color: {colors['on_surface_variant'].name()};
            }}
            
            QMenu::separator {{
                height: 1px;
                background: {colors['outline'].name()};
                margin: {spacing_md}px 0;
            }}
            
            /* Toolbars */
            QToolBar {{
                background-color: {colors['surface'].name()};
                border: none;
                padding: {spacing_md}px;
                spacing: {spacing_md}px;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {colors['primary'].name()};
                color: white;
                border: none;
                border-radius: {border_radius}px;
                padding: {spacing_md}px {spacing_lg}px;
                font-size: 14px;
                font-weight: 600;
                min-height: 32px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['primary_hover'].name()};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['primary_pressed'].name()};
            }}
            
            QPushButton:disabled {{
                background-color: {colors['secondary'].name()};
                color: {colors['on_surface_variant'].name()};
            }}
            
            QPushButton#secondary {{
                background-color: {colors['secondary'].name()};
                color: {colors['on_surface'].name()};
            }}
            
            QPushButton#secondary:hover {{
                background-color: {colors['surface_variant'].name()};
            }}
            
            /* Labels */
            QLabel#panel-title {{
                font-size: 16px;
                font-weight: 600;
                padding: {spacing_md}px 0;
                border-bottom: 1px solid {colors['outline'].name()};
                color: {colors['on_surface'].name()};
            }}
            
            /* Progress bars */
            QProgressBar {{
                border: 1px solid {colors['outline'].name()};
                border-radius: {border_radius}px;
                text-align: center;
                background-color: {colors['secondary'].name()};
                height: 20px;
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['primary'].name()};
                border-radius: {border_radius - 1}px;
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                border: none;
                background: {colors['secondary'].name()};
                width: 14px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {colors['surface_variant'].name()};
                border-radius: 7px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {colors['primary'].name()};
            }}
            
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
                border: none;
                background: none;
                height: 0;
            }}
            
            QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical {{
                background: none;
            }}
        """

class ProjectArea(QWidget):
    """Project area showing file queue and project status with Fluent Design."""
    
    file_added = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the project area UI with Fluent Design."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg")
        )
        layout.setSpacing(FluentDesignSystem.get_spacing("md"))
        
        # Title
        title = QLabel("Project Files")
        title.setObjectName("panel-title")
        title.setFont(FluentDesignSystem.get_font("title_small"))
        layout.addWidget(title)
        
        # File list area (placeholder)
        self.file_list = QLabel("No files added yet")
        self.file_list.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list.setFont(FluentDesignSystem.get_font("body_medium"))
        self.file_list.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {FluentDesignSystem.get_theme_colors()["outline"].name()};
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("xl")}px;
                color: {FluentDesignSystem.get_theme_colors()["on_surface_variant"].name()};
                background-color: {FluentDesignSystem.get_theme_colors()["surface_variant"].name()};
            }}
        """)
        layout.addWidget(self.file_list)
        
        # Add file button
        self.add_file_btn = QPushButton("Add Audio/Video File")
        self.add_file_btn.setFont(FluentDesignSystem.get_font("button"))
        self.add_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_file_btn.clicked.connect(self.add_file)
        self.add_file_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary"].name()};
                color: white;
                border: none;
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("md")}px {FluentDesignSystem.get_spacing("lg")}px;
                font-size: 14px;
                font-weight: 600;
                min-height: 32px;
                transition: all 0.2s ease;
            }}
            
            QPushButton:hover {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary_hover"].name()};
                transform: scale(1.02);
            }}
            
            QPushButton:pressed {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary_pressed"].name()};
                transform: scale(0.98);
            }}
            
            QPushButton:disabled {{
                background-color: {FluentDesignSystem.get_theme_colors()["secondary"].name()};
                color: {FluentDesignSystem.get_theme_colors()["on_surface_variant"].name()};
            }}
        """)
        layout.addWidget(self.add_file_btn)
        
        layout.addStretch()
    
    def add_file(self):
        """Open file dialog to add a new file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Audio or Video File",
            "",
            "Audio/Video Files (*.mp3 *.wav *.mp4 *.mov *.avi *.mkv *.flac *.m4a *.aac *.ogg *.wma *.flv *.webm)"
        )
        
        if file_path:
            self.file_added.emit(file_path)

from .waveform_widget import WaveformWidget

class ProcessPanel(QWidget):
    """Process panel showing audio timeline and waveform with Fluent Design."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the process panel UI with Fluent Design."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg")
        )
        layout.setSpacing(FluentDesignSystem.get_spacing("md"))
        
        # Title
        title = QLabel("Audio Processing")
        title.setObjectName("panel-title")
        title.setFont(FluentDesignSystem.get_font("title_small"))
        layout.addWidget(title)
        
        # Waveform visualization
        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFont(FluentDesignSystem.get_font("caption"))
        layout.addWidget(self.progress)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(FluentDesignSystem.get_spacing("md"))
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setFont(FluentDesignSystem.get_font("button"))
        self.play_btn.setMinimumWidth(100)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary"].name()};
                color: white;
                border: none;
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("md")}px {FluentDesignSystem.get_spacing("lg")}px;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s ease;
            }}
            
            QPushButton:hover {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary_hover"].name()};
                transform: scale(1.02);
            }}
            
            QPushButton:pressed {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary_pressed"].name()};
                transform: scale(0.98);
            }}
        """)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setFont(FluentDesignSystem.get_font("button"))
        self.pause_btn.setMinimumWidth(100)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {FluentDesignSystem.get_theme_colors()["secondary"].name()};
                color: {FluentDesignSystem.get_theme_colors()["on_surface"].name()};
                border: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("md")}px {FluentDesignSystem.get_spacing("lg")}px;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s ease;
            }}
            
            QPushButton:hover {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface_variant"].name()};
                transform: scale(1.02);
            }}
            
            QPushButton:pressed {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary"].name()};
                color: white;
                transform: scale(0.98);
            }}
        """)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFont(FluentDesignSystem.get_font("button"))
        self.stop_btn.setMinimumWidth(100)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface_variant"].name()};
                color: {FluentDesignSystem.get_theme_colors()["on_surface"].name()};
                border: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("md")}px {FluentDesignSystem.get_spacing("lg")}px;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s ease;
            }}
            
            QPushButton:hover {{
                background-color: {FluentDesignSystem.get_theme_colors()["error"].name()};
                color: white;
                transform: scale(1.02);
            }}
            
            QPushButton:pressed {{
                background-color: {FluentDesignSystem.get_theme_colors()["error"].name()};
                color: white;
                transform: scale(0.98);
            }}
        """)
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)

class MainWindow(QMainWindow):
    """Main application window with modern Fluent/WinUI design."""
    
    progress_updated = pyqtSignal(ProcessingState)
    processing_finished = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.settings
        self.pipeline = StreamingPipeline(
            workspace_dir=os.path.join(os.getcwd(), "workspace"),
            settings=self.settings
        )
        self.audio_player = AudioPlayer()
        self.current_file = None
        self.tour_manager = TourManager(self)
        self.contextual_help = ContextualHelp()
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_tour()
        self.apply_theme()
        
        # Connect pipeline signals
        self.progress_updated.connect(self.on_processing_progress)
        self.processing_finished.connect(self.on_processing_finished)
        self.pipeline.set_progress_callback(self.progress_updated.emit)
        self.pipeline.set_completion_callback(lambda fp, res: self.processing_finished.emit(res))
        
        # Start pipeline workers
        self.pipeline.start_workers()

    def closeEvent(self, event):
        """Handle window close event to stop workers."""
        self.pipeline.stop_workers()
        event.accept()
    
    def setup_ui(self):
        """Set up the main UI layout with Fluent Design and Windows effects."""
        self.setWindowTitle("Transcriptor de Video/Audio")
        
        # Set responsive window size based on screen dimensions
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        
        # Use 80% of screen size, but not larger than 1400x900
        width = min(int(screen_size.width() * 0.8), 1400)
        height = min(int(screen_size.height() * 0.8), 900)
        
        self.resize(width, height)
        
        # Center the window on screen
        self.move(
            (screen_size.width() - width) // 2,
            (screen_size.height() - height) // 2
        )
        
        # Apply Windows Fluent effects if supported
        if WindowsFluentEffects.is_supported():
            WindowsFluentEffects.apply_mica_effect(self)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(FluentDesignSystem.get_spacing("md"))
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {FluentDesignSystem.get_theme_colors()["outline"].name()};
            }}
            QSplitter::handle:hover {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary"].name()};
            }}
        """)
        main_layout.addWidget(splitter)
        
        # Create the three main panels
        self.project_area = ProjectArea()
        self.project_area.file_added.connect(self.on_file_added)
        
        self.process_panel = ProcessPanel()
        self.transcription_editor = TranscriptionEditor()

        # Connect audio player signals and controls
        self.process_panel.play_btn.clicked.connect(self.audio_player.play)
        self.process_panel.pause_btn.clicked.connect(self.audio_player.pause)
        self.process_panel.stop_btn.clicked.connect(self.audio_player.stop)
        self.audio_player.position_changed.connect(self.update_ui_on_playback)
        self.process_panel.waveform.position_clicked.connect(lambda pos: self.audio_player.seek(int(pos * 1000)))
        
        # Add panels to splitter
        splitter.addWidget(self.project_area)
        splitter.addWidget(self.process_panel)
        splitter.addWidget(self.transcription_editor)
        
        # Set initial sizes based on window width
        total_width = width
        project_width = max(200, int(total_width * 0.2))  # 20% or minimum 200px
        process_width = int(total_width * 0.4)  # 40%
        editor_width = total_width - project_width - process_width  # Remaining space
        
        splitter.setSizes([project_width, process_width, editor_width])
        
        # Set object names for styling
        self.project_area.setObjectName("project-area")
        self.process_panel.setObjectName("process-panel")
        self.transcription_editor.setObjectName("transcription-editor")
        
        # Connect resize event for responsive adjustments
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle events for responsive design."""
        if obj == self and event.type() == event.Type.Resize:
            # Adjust UI elements based on new window size
            self._adjust_layout_for_size()
        return super().eventFilter(obj, event)
    
    def _adjust_layout_for_size(self):
        """Adjust layout based on current window size."""
        # Get current window dimensions
        width = self.width()
        
        # Adjust project area width based on window size
        splitter = self.centralWidget().layout().itemAt(0).widget()
        if splitter and isinstance(splitter, QSplitter):
            # For smaller windows, reduce project area width
            if width < 1000:
                project_width = max(150, int(width * 0.15))  # 15% or minimum 150px
                process_width = int(width * 0.35)  # 35%
                editor_width = width - project_width - process_width  # Remaining space
                splitter.setSizes([project_width, process_width, editor_width])
            elif width > 1600:
                # For larger windows, increase project area width
                project_width = min(300, int(width * 0.15))  # 15% or maximum 300px
                process_width = int(width * 0.35)  # 35%
                editor_width = width - project_width - process_width  # Remaining space
                splitter.setSizes([project_width, process_width, editor_width])
    
    def setup_menu(self):
        """Set up the application menu with Fluent Design."""
        menu_bar = self.menuBar()
        menu_bar.setFont(FluentDesignSystem.get_font("body_medium"))
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.setFont(FluentDesignSystem.get_font("body_medium"))
        
        import_action = QAction("&Import Audio/Video...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setFont(FluentDesignSystem.get_font("body_medium"))
        import_action.triggered.connect(self.import_file)
        file_menu.addAction(import_action)

        export_menu = file_menu.addMenu("&Export")
        export_srt_action = QAction("Export as SRT...", self)
        export_srt_action.triggered.connect(self.export_srt)
        export_menu.addAction(export_srt_action)

        export_vtt_action = QAction("Export as VTT...", self)
        export_vtt_action.triggered.connect(self.export_vtt)
        export_menu.addAction(export_vtt_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setFont(FluentDesignSystem.get_font("body_medium"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.setFont(FluentDesignSystem.get_font("body_medium"))

        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        view_menu.setFont(FluentDesignSystem.get_font("body_medium"))
        
        # Settings menu
        settings_menu = menu_bar.addMenu("&Settings")
        settings_menu.setFont(FluentDesignSystem.get_font("body_medium"))
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.setFont(FluentDesignSystem.get_font("body_medium"))
        
        about_action = QAction("&About", self)
        about_action.setFont(FluentDesignSystem.get_font("body_medium"))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Set up the application toolbar with Fluent Design."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface"].name()};
                border: none;
                padding: {FluentDesignSystem.get_spacing("sm")}px;
                spacing: {FluentDesignSystem.get_spacing("sm")}px;
            }}
            
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: {FluentDesignSystem.get_border_radius("sm")}px;
                padding: {FluentDesignSystem.get_spacing("sm")}px;
                margin: 0;
            }}
            
            QToolButton:hover {{
                background-color: {FluentDesignSystem.get_theme_colors()["secondary"].name()};
            }}
            
            QToolButton:pressed {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary"].name()};
                color: white;
            }}
        """)
        self.addToolBar(toolbar)
        
        # Add actions to toolbar
        import_action = QAction(QIcon.fromTheme("document-open"), "Import", self)
        import_action.triggered.connect(self.import_file)
        toolbar.addAction(import_action)
    
    def setup_status_bar(self):
        """Set up the status bar with Fluent Design."""
        self.status_bar = QStatusBar()
        self.status_bar.setFont(FluentDesignSystem.get_font("caption"))
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface"].name()};
                border-top: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                padding: {FluentDesignSystem.get_spacing("sm")}px;
            }}
            
            QLabel {{
                color: {FluentDesignSystem.get_theme_colors()["on_surface_variant"].name()};
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def apply_theme(self):
        """Apply the configured theme."""
        theme = self.config_manager.settings.theme
        ThemeManager.apply_theme(QApplication.instance(), theme)
    
    def import_file(self):
        """Import an audio or video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Audio or Video File",
            "",
            "Audio/Video Files (*.mp3 *.wav *.mp4 *.mov *.avi *.mkv *.flac *.m4a *.aac *.ogg *.wma *.flv *.webm)"
        )
        
        if file_path:
            self.on_file_added(file_path)
    
    def on_file_added(self, file_path):
        """Handle file added event by starting the processing pipeline."""
        self.current_file = file_path
        self.status_bar.showMessage(f"Starting processing for: {os.path.basename(file_path)}")
        self.process_panel.progress.setValue(0)
        
        # Start the pipeline for the new file
        self.pipeline.start_processing(file_path)

    def on_processing_progress(self, state: ProcessingState):
        """Handle progress updates from the pipeline."""
        if state.file_path != self.current_file:
            return  # Ignore updates for other files

        # Update status message
        status_message = f"{state.stage.value.replace('_', ' ').title()}: {state.status}..."
        self.status_bar.showMessage(status_message)
        
        # Update progress bar
        # We can map stages to progress bar values
        stage_progress = {
            "extract_audio": 25,
            "vad_segmentation": 50,
            "transcription": 75,
            "alignment": 90,
            "merge_segments": 95,
            "export": 100
        }
        
        base_progress = stage_progress.get(state.stage.value, 0)
        
        if state.status == "running":
            # Calculate progress within the stage
            stage_total = stage_progress.get(state.stage.value, 25)
            prev_stage_total = list(stage_progress.values())[list(stage_progress.keys()).index(state.stage.value) - 1] if state.stage.value != "extract_audio" else 0
            progress = prev_stage_total + (stage_total - prev_stage_total) * state.progress
            self.process_panel.progress.setValue(int(progress))
        elif state.status == "completed":
            self.process_panel.progress.setValue(base_progress)
            if state.stage == ProcessingStage.EXTRACT_AUDIO:
                self.process_panel.waveform.load_audio(state.result)
                self.audio_player.load(state.result)
            elif state.stage == ProcessingStage.EXPORT:
                self.on_processing_finished(state.result)
        elif state.status == "failed":
            self.status_bar.showMessage(f"Error during {state.stage.value}: {state.error}")
            self.process_panel.progress.setValue(0)

    def on_processing_finished(self, final_result):
        """Handle processing completion and load real data into the editor."""
        self.process_panel.progress.setValue(100)
        self.status_bar.showMessage("Processing complete. Loading editor...")

        # Convert the raw dictionary result from the pipeline into Segment and Word objects
        segments_to_load = []
        if final_result:
            for i, seg_dict in enumerate(final_result):
                words_to_load = []
                if 'words' in seg_dict and seg_dict['words']:
                    for word_dict in seg_dict['words']:
                        words_to_load.append(Word(
                            text=word_dict.get('word', ''),
                            start_time=word_dict.get('start', 0.0),
                            end_time=word_dict.get('end', 0.0),
                            confidence=word_dict.get('score', 0.0), # Use 'score' from whisperx for confidence
                            speaker=word_dict.get('speaker', 'UNKNOWN')
                        ))
                
                segments_to_load.append(Segment(
                    id=i,
                    start_time=seg_dict.get('start', 0.0),
                    end_time=seg_dict.get('end', 0.0),
                    words=words_to_load,
                    text=seg_dict.get('text', '')
                ))

        # Load the real data into the editor
        self.transcription_editor.load_transcription(segments_to_load)
        self.status_bar.showMessage("Transcription loaded successfully.")

    def update_ui_on_playback(self, position_ms: int):
        """Update UI elements based on audio playback position."""
        position_s = position_ms / 1000.0
        self.process_panel.waveform.set_cursor_position(position_s)
        self.transcription_editor.highlight_word_at_time(position_s)
    
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Transcriptor",
            (
                "Transcriptor de Video/Audio\n\n"
                "A high-fidelity transcription application using Whisper, PyQt6, and modern AI techniques.\n\n"
                "Features:\n"
                "• Local processing with Whisper Large v3\n"
                "• Word-level alignment with WhisperX\n"
                "• Speaker diarization with pyannote.audio\n"
                "• Audio preprocessing with FFmpeg\n"
                "• Modern Fluent/WinUI interface\n"
            )
        )
    
    def setup_tour(self):
        """Set up the guided tour for new users with enhanced visuals."""
        # Add tour steps with more detailed descriptions
        self.tour_manager.add_step(
            self.project_area.add_file_btn,
            "Add Files",
            "Start by adding audio or video files to transcribe. Click this button to select files from your computer. "
            "The application supports a wide range of formats including MP3, WAV, MP4, MOV, AVI, and MKV."
        )
        
        self.tour_manager.add_step(
            self.process_panel.waveform,
            "Audio Processing",
            "This panel shows the audio waveform and processing progress. You can play, pause, and stop audio playback here. "
            "The progress bar indicates the transcription status, and the waveform visualization helps you navigate through the audio."
        )
        
        self.tour_manager.add_step(
            self.transcription_editor.segments_tree,
            "Transcription Structure",
            "The left panel shows the transcription structure with segments and words. Each segment has a start and end time, "
            "and you can see which speaker said what. Click on any segment to jump to that part of the audio."
        )
        
        self.tour_manager.add_step(
            self.transcription_editor.text_editor,
            "Transcription Editor",
            "The transcription appears here with precise timing. Words are color-coded by confidence level and speaker. "
            "You can edit the text directly and adjust timing as needed. Right-click for additional options."
        )
        
        # Add contextual help with more detailed information
        self.contextual_help.add_help_text(
            self.project_area.add_file_btn,
            "Click to add audio or video files for transcription.\n"
            "Supported formats: MP3, WAV, MP4, MOV, AVI, MKV, FLAC, M4A, AAC, OGG, WMA, FLV, WEBM"
        )
        
        self.contextual_help.add_help_text(
            self.process_panel.waveform,
            "Visualizes the audio waveform and shows processing progress.\n"
            "Click and drag to navigate through the audio. The highlighted area shows the current playback position."
        )
        
        self.contextual_help.add_help_text(
            self.process_panel.progress,
            "Shows the transcription progress.\n"
            "The bar fills as the transcription completes. Click 'Pause' to temporarily stop processing."
        )
        
        self.contextual_help.add_help_text(
            self.transcription_editor.segments_tree,
            "Shows the transcription structure with segments and words.\n"
            "Each row represents a segment with timing information. Expand segments to see individual words."
        )
        
        self.contextual_help.add_help_text(
            self.transcription_editor.text_editor,
            "Edit the transcription text directly.\n"
            "Words are color-coded by confidence (green = high, orange = medium, red = low). "
            "Right-click for playback and editing options."
        )
        
        # Start tour automatically for new users with a smoother introduction
        if self.config_manager.settings.show_guided_tours:
            QTimer.singleShot(2000, self.tour_manager.start_tour)

    def export_srt(self):
        """Export transcription to SRT file."""
        if not self.transcription_editor.segments:
            QMessageBox.warning(self, "Export Error", "There is no transcription to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export SRT",
            f"{os.path.splitext(os.path.basename(self.current_file))[0]}.srt",
            "SubRip Subtitle files (*.srt)"
        )

        if file_path:
            self.transcription_editor.export_srt(file_path)
            self.status_bar.showMessage(f"Exported to {file_path}")

    def export_vtt(self):
        """Export transcription to VTT file."""
        if not self.transcription_editor.segments:
            QMessageBox.warning(self, "Export Error", "There is no transcription to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export VTT",
            f"{os.path.splitext(os.path.basename(self.current_file))[0]}.vtt",
            "WebVTT files (*.vtt)"
        )

        if file_path:
            self.transcription_editor.export_vtt(file_path)
            self.status_bar.showMessage(f"Exported to {file_path}")

    def open_settings_dialog(self):
        """Open the settings dialog and update the pipeline if settings change."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.get_settings()
            self.config_manager.settings = self.settings
            self.config_manager.save_settings()
            
            # Re-initialize the pipeline with new settings
            self.pipeline.stop_workers()
            self.pipeline = StreamingPipeline(
                workspace_dir=os.path.join(os.getcwd(), "workspace"),
                settings=self.settings
            )
            self.pipeline.set_progress_callback(self.progress_updated.emit)
            self.pipeline.set_completion_callback(lambda fp, res: self.processing_finished.emit(res))
            self.pipeline.start_workers()
            
            self.status_bar.showMessage("Settings updated. Pipeline re-initialized.")
