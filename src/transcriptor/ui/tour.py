"""
Guided tours and contextual help system for the Transcriptor application.
"""
import sys
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGraphicsOpacityEffect, QApplication, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QPalette, QColor, QPainter, QPen, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QTimer, QEasingCurve, QPropertyAnimation, pyqtProperty
from .fluent_design import FluentDesignSystem

class CoachMark(QWidget):
    """A coach mark that highlights a specific area of the UI with an overlay."""
    
    finished = pyqtSignal()
    
    def __init__(self, target_widget, title, description, parent=None):
        super().__init__(parent)
        self.target_widget = target_widget
        self.title = title
        self.description = description
        self.next_button = None
        self.skip_button = None
        
        # Make it transparent and frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Calculate position
        self.calculate_position()
        
        # Set up UI
        self.setup_ui()
        
        # Fade in animation with scaling effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Opacity animation
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(400)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(0.9)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Scale animation for content widget
        self.content_widget = None  # Will be set in setup_ui
        
        self.fade_in_animation.start()
    
    def calculate_position(self):
        """Calculate the position and size of the coach mark."""
        if self.target_widget:
            # Get global position of target widget
            global_pos = self.target_widget.mapToGlobal(QPoint(0, 0))
            size = self.target_widget.size()
            
            # Set our geometry to cover the entire screen
            screen_geo = QApplication.primaryScreen().geometry()
            self.setGeometry(screen_geo)
            
            # Store the target rect in global coordinates
            self.target_rect = QRect(global_pos, size)
        else:
            # Full screen overlay
            screen_geo = QApplication.primaryScreen().geometry()
            self.setGeometry(screen_geo)
            self.target_rect = QRect(0, 0, 0, 0)
    
    def setup_ui(self):
        """Set up the coach mark UI with Fluent Design."""
        # Get theme colors
        colors = FluentDesignSystem.get_theme_colors("dark")  # Always use dark for coach marks
        border_radius = FluentDesignSystem.get_border_radius("lg")
        spacing_md = FluentDesignSystem.get_spacing("md")
        spacing_lg = FluentDesignSystem.get_spacing("lg")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Spacer to push content to the right position
        spacer_top = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(spacer_top)
        
        # Content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['surface_variant'].name()};
                border-radius: {border_radius}px;
                border: 1px solid {colors['outline'].name()};
                box-shadow: {FluentDesignSystem.ELEVATION['level4']};
            }}
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(spacing_lg, spacing_lg, spacing_lg, spacing_lg)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(FluentDesignSystem.get_font("title_medium"))
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['on_surface'].name()};
                margin-bottom: {spacing_md}px;
            }}
        """)
        content_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setFont(FluentDesignSystem.get_font("body_medium"))
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['on_surface_variant'].name()};
                margin-bottom: {spacing_lg}px;
            }}
        """)
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(spacing_md)
        
        self.skip_button = QPushButton("Skip Tour")
        self.skip_button.setFont(FluentDesignSystem.get_font("button"))
        self.skip_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors['on_surface_variant'].name()};
                border: none;
                padding: {spacing_md}px {spacing_lg}px;
                border-radius: {FluentDesignSystem.get_border_radius("sm")}px;
            }}
            QPushButton:hover {{
                background-color: {colors['secondary'].name()};
                color: {colors['on_surface'].name()};
            }}
        """)
        self.skip_button.clicked.connect(self.skip_tour)
        
        self.next_button = QPushButton("Next")
        self.next_button.setFont(FluentDesignSystem.get_font("button"))
        self.next_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary'].name()};
                color: white;
                border: none;
                padding: {spacing_md}px {spacing_lg}px;
                border-radius: {FluentDesignSystem.get_border_radius("sm")}px;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover'].name()};
            }}
            QPushButton:pressed {{
                background-color: {colors['primary_pressed'].name()};
            }}
        """)
        self.next_button.clicked.connect(self.next_step)
        
        button_layout.addWidget(self.skip_button)
        button_layout.addStretch()
        button_layout.addWidget(self.next_button)
        
        content_layout.addLayout(button_layout)
        
        # Store reference to content widget for animations
        self.content_widget = content_widget
        
        # Add content widget to main layout
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        spacer_left = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        h_layout.addItem(spacer_left)
        
        # Position content near target
        if self.target_widget:
            h_layout.addWidget(content_widget)
            # Adjust position based on target location
            target_center = self.target_rect.center()
            if target_center.x() > self.width() / 2:
                # Target is on the right side, put content on the left
                h_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        
        spacer_right = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        h_layout.addItem(spacer_right)
        
        main_layout.addLayout(h_layout)
        
        # Add subtle entrance animation for content
        if self.content_widget:
            self.content_widget.setGraphicsEffect(QGraphicsOpacityEffect())
            content_effect = self.content_widget.graphicsEffect()
            content_effect.setOpacity(0)
            
            # Content fade in
            self.content_fade_animation = QPropertyAnimation(content_effect, b"opacity")
            self.content_fade_animation.setDuration(300)
            self.content_fade_animation.setStartValue(0)
            self.content_fade_animation.setEndValue(1)
            self.content_fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
            
            # Delay content animation slightly
            QTimer.singleShot(100, self.content_fade_animation.start)
        
        spacer_bottom = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(spacer_bottom)
    
    def paintEvent(self, event):
        """Paint the overlay and highlight with Fluent Design."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw semi-transparent overlay with Fluent color
        overlay_color = FluentDesignSystem.get_theme_colors("dark")["background"]
        painter.setBrush(QColor(overlay_color.red(), overlay_color.green(), overlay_color.blue(), 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # Highlight the target area
        if self.target_rect.width() > 0 and self.target_rect.height() > 0:
            # Convert global target rect to local coordinates
            local_target = QRect(
                self.target_rect.x() - self.x(),
                self.target_rect.y() - self.y(),
                self.target_rect.width(),
                self.target_rect.height()
            )
            
            # Draw highlight around target with Fluent accent color
            highlight_color = FluentDesignSystem.get_theme_colors("dark")["primary"]
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setBrush(QColor(0, 0, 0, 0))  # Transparent fill
            pen = QPen(highlight_color, 3)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawRoundedRect(local_target, 
                                  FluentDesignSystem.get_border_radius("md"), 
                                  FluentDesignSystem.get_border_radius("md"))
    
    def next_step(self):
        """Proceed to the next step in the tour with animation."""
        # Add a subtle press animation
        self.next_button.setDown(True)
        QTimer.singleShot(50, lambda: self.next_button.setDown(False))
        QTimer.singleShot(150, lambda: self.fade_out())
    
    def skip_tour(self):
        """Skip the entire tour with animation."""
        # Add a subtle press animation
        self.skip_button.setDown(True)
        QTimer.singleShot(50, lambda: self.skip_button.setDown(False))
        QTimer.singleShot(150, lambda: self.fade_out())
        self.finished.emit()
    
    def fade_out(self):
        """Fade out the coach mark with smooth animations."""
        # Fade out both the overlay and content
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(0.9)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Content fade out
        if self.content_widget:
            content_effect = self.content_widget.graphicsEffect()
            self.content_fade_out_animation = QPropertyAnimation(content_effect, b"opacity")
            self.content_fade_out_animation.setDuration(200)
            self.content_fade_out_animation.setStartValue(1)
            self.content_fade_out_animation.setEndValue(0)
            self.content_fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self.content_fade_out_animation.start()
        
        self.fade_out_animation.finished.connect(self.close_and_emit)
        self.fade_out_animation.start()
    
    def close_and_emit(self):
        """Close the widget and emit the finished signal."""
        self.close()
        self.finished.emit()

class TourManager:
    """Manages guided tours for the application."""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.tour_steps = []
        self.current_step = 0
        self.active_coach_mark = None
    
    def add_step(self, target_widget, title, description):
        """Add a step to the tour."""
        self.tour_steps.append({
            'widget': target_widget,
            'title': title,
            'description': description
        })
    
    def start_tour(self):
        """Start the guided tour."""
        self.current_step = 0
        self.show_step()
    
    def show_step(self):
        """Show the current step of the tour."""
        if self.current_step >= len(self.tour_steps):
            # Tour completed
            return
            
        step = self.tour_steps[self.current_step]
        
        # Create coach mark
        self.active_coach_mark = CoachMark(
            step['widget'],
            step['title'],
            step['description'],
            self.parent_window
        )
        
        self.active_coach_mark.finished.connect(self.on_step_finished)
        self.active_coach_mark.show()
    
    def on_step_finished(self):
        """Handle completion of a tour step."""
        self.current_step += 1
        self.show_step()
    
    def skip_tour(self):
        """Skip the entire tour."""
        if self.active_coach_mark:
            self.active_coach_mark.close()
        self.current_step = len(self.tour_steps)  # Mark as completed

class ContextualHelp:
    """Provides contextual help for UI elements."""
    
    def __init__(self):
        self.help_texts = {}
    
    def add_help_text(self, widget, text):
        """Add help text for a widget."""
        self.help_texts[widget] = text
        widget.setWhatsThis(text)
    
    def show_help_for_widget(self, widget):
        """Show help for a specific widget."""
        if widget in self.help_texts:
            # In a real implementation, you might show a tooltip or dialog
            # For now, we'll just print to console
            print(f"Help for {widget.objectName()}: {self.help_texts[widget]}")