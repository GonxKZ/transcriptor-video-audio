"""
Advanced transcription editor with WYSIWYG functionality.
"""
import sys
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QMenu, QApplication
)
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QAction, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from .fluent_design import FluentDesignSystem
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Word:
    """Represents a word in the transcription."""
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker: Optional[str] = None
    char_start_pos: int = 0
    char_end_pos: int = 0

@dataclass
class Segment:
    """Represents a segment in the transcription."""
    id: int
    start_time: float
    end_time: float
    words: List[Word]
    text: str = ""

class TranscriptionEditor(QWidget):
    """Advanced transcription editor with WYSIWYG functionality."""
    
    # Signals
    word_selected = pyqtSignal(float, float)  # start_time, end_time
    segment_selected = pyqtSignal(int)  # segment_id
    text_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.segments: List[Segment] = []
        self.current_segment_id: Optional[int] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the editor UI with Fluent Design."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg"),
            FluentDesignSystem.get_spacing("lg")
        )
        layout.setSpacing(FluentDesignSystem.get_spacing("md"))
        
        # Create splitter for tree view and text editor
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
        layout.addWidget(splitter)
        
        # Segments tree view
        self.segments_tree = QTreeWidget()
        self.segments_tree.setHeaderLabels(["Segment", "Start", "End", "Speaker", "Text"])
        self.segments_tree.setFont(FluentDesignSystem.get_font("body_medium"))
        self.segments_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.segments_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.segments_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.segments_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.segments_tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.segments_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface"].name()};
                alternate-background-color: {FluentDesignSystem.get_theme_colors()["surface_variant"].name()};
                border: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("sm")}px;
            }}
            
            QTreeWidget::item {{
                padding: {FluentDesignSystem.get_spacing("sm")}px;
                border-radius: {FluentDesignSystem.get_border_radius("sm")}px;
            }}
            
            QTreeWidget::item:hover {{
                background-color: {FluentDesignSystem.get_theme_colors()["secondary"].name()};
            }}
            
            QTreeWidget::item:selected {{
                background-color: {FluentDesignSystem.get_theme_colors()["primary"].name()};
                color: white;
            }}
            
            QHeaderView::section {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface_variant"].name()};
                color: {FluentDesignSystem.get_theme_colors()["on_surface"].name()};
                padding: {FluentDesignSystem.get_spacing("sm")}px;
                border: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                font-weight: 600;
            }}
        """)
        splitter.addWidget(self.segments_tree)
        
        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setFont(FluentDesignSystem.get_font("body_large"))
        self.text_editor.textChanged.connect(self.on_text_changed)
        self.text_editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_editor.customContextMenuRequested.connect(self.show_text_context_menu)
        self.text_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface"].name()};
                color: {FluentDesignSystem.get_theme_colors()["on_surface"].name()};
                border: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("md")}px;
                selection-background-color: {FluentDesignSystem.get_theme_colors()["primary"].name()};
                selection-color: white;
            }}
            
            QTextEdit:focus {{
                border: 2px solid {FluentDesignSystem.get_theme_colors()["primary"].name()};
            }}
        """)
        splitter.addWidget(self.text_editor)
        
        # Set initial sizes
        splitter.setSizes([300, 700])
        
        # Connect cursor position changes
        self.text_editor.cursorPositionChanged.connect(self.on_cursor_position_changed)
        
    def load_transcription(self, segments: List[Segment]):
        """
        Load transcription segments into the editor.
        
        Args:
            segments: List of transcription segments
        """
        self.segments = segments
        self.update_tree_view()
        self.update_text_editor()
        
    def update_tree_view(self):
        """Update the segments tree view."""
        self.segments_tree.clear()
        
        for segment in self.segments:
            # Create segment item
            segment_item = QTreeWidgetItem([
                str(segment.id),
                f"{segment.start_time:.2f}",
                f"{segment.end_time:.2f}",
                segment.words[0].speaker if segment.words and segment.words[0].speaker else "",
                segment.text
            ])
            segment_item.setData(0, Qt.ItemDataRole.UserRole, segment.id)
            self.segments_tree.addTopLevelItem(segment_item)
            
            # Add word sub-items
            for word in segment.words:
                word_item = QTreeWidgetItem([
                    "",
                    f"{word.start_time:.2f}",
                    f"{word.end_time:.2f}",
                    word.speaker or "",
                    word.text
                ])
                word_item.setData(0, Qt.ItemDataRole.UserRole, f"{segment.id}:{word.start_time}")
                segment_item.addChild(word_item)
                
    def update_text_editor(self):
        """Update the text editor with formatted transcription."""
        self.text_editor.clear()
        self.current_highlighted_word = None
        
        cursor = self.text_editor.textCursor()
        
        for segment in self.segments:
            for i, word in enumerate(segment.words):
                # Store character position
                word.char_start_pos = cursor.position()
                
                # Set format
                format = self.get_word_format(word)
                cursor.insertText(word.text, format)
                word.char_end_pos = cursor.position()
                
                # Add space
                if i < len(segment.words) - 1:
                    cursor.insertText(" ")
            
            # Add newline after segment
            cursor.insertText("\n\n")

    def get_word_format(self, word: Word, highlighted: bool = False) -> QTextCharFormat:
        """Get the character format for a given word."""
        format = QTextCharFormat()
        
        # Highlight format
        if highlighted:
            format.setBackground(QColor("#FFFF00")) # Yellow
            format.setFontWeight(QFont.Weight.Bold)
            return format

        # Confidence color
        if word.confidence < 0.5:
            format.setForeground(QColor("red"))
        elif word.confidence < 0.8:
            format.setForeground(QColor("orange"))
        else:
            format.setForeground(QColor("black"))
            
        # Speaker color
        if word.speaker:
            speaker_colors = {
                "SPEAKER_00": QColor(200, 230, 255),  # Light blue
                "SPEAKER_01": QColor(255, 230, 200),  # Light orange
                "SPEAKER_02": QColor(230, 255, 200),  # Light green
            }
            color = speaker_colors.get(word.speaker, QColor(240, 240, 240))
            format.setBackground(color)
        else:
            format.setBackground(QColor("white"))
            
        return format

    def highlight_word_at_time(self, time_s: float):
        """Highlight the word being spoken at a given time."""
        word_to_highlight = None
        for segment in self.segments:
            if segment.start_time <= time_s <= segment.end_time:
                for word in segment.words:
                    if word.start_time <= time_s <= word.end_time:
                        word_to_highlight = word
                        break
            if word_to_highlight:
                break

        if word_to_highlight != self.current_highlighted_word:
            # Remove old highlight
            if self.current_highlighted_word:
                self.apply_format_to_word(self.current_highlighted_word, highlighted=False)
            
            # Apply new highlight
            if word_to_highlight:
                self.apply_format_to_word(word_to_highlight, highlighted=True)
            
            self.current_highlighted_word = word_to_highlight

    def apply_format_to_word(self, word: Word, highlighted: bool):
        """Apply a specific format to a word in the editor."""
        cursor = self.text_editor.textCursor()
        cursor.setPosition(word.char_start_pos)
        cursor.setPosition(word.char_end_pos, QTextCursor.MoveMode.KeepAnchor)
        
        format = self.get_word_format(word, highlighted)
        cursor.setCharFormat(format)
            
    def on_tree_selection_changed(self):
        """Handle tree view selection changes."""
        selected_items = self.segments_tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Check if it's a segment or word
        if isinstance(data, int):
            # Segment selected
            self.segment_selected.emit(data)
            self.current_segment_id = data
        elif isinstance(data, str) and ":" in data:
            # Word selected
            parts = data.split(":")
            segment_id = int(parts[0])
            start_time = float(parts[1])
            
            # Find the word and emit signal
            for segment in self.segments:
                if segment.id == segment_id:
                    for word in segment.words:
                        if abs(word.start_time - start_time) < 0.01:  # Small tolerance
                            self.word_selected.emit(word.start_time, word.end_time)
                            break
                    break
                    
    def on_text_changed(self):
        """Handle text changes in the editor."""
        self.text_changed.emit()
        
    def on_cursor_position_changed(self):
        """Handle cursor position changes."""
        # In a full implementation, this would highlight the corresponding word
        # in the tree view and possibly in the audio waveform
        pass
        
    def show_tree_context_menu(self, position):
        """Show context menu for tree view with Fluent Design."""
        item = self.segments_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        menu.setFont(FluentDesignSystem.get_font("body_medium"))
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface"].name()};
                border: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("sm")}px 0;
            }}
            
            QMenu::item {{
                padding: {FluentDesignSystem.get_spacing("sm")}px {FluentDesignSystem.get_spacing("lg")}px;
                color: {FluentDesignSystem.get_theme_colors()["on_surface"].name()};
            }}
            
            QMenu::item:selected {{
                background-color: {FluentDesignSystem.get_theme_colors()["secondary"].name()};
            }}
            
            QMenu::separator {{
                height: 1px;
                background: {FluentDesignSystem.get_theme_colors()["outline"].name()};
                margin: {FluentDesignSystem.get_spacing("sm")}px 0;
            }}
        """)
        
        # Add actions based on item type
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, int):
            # Segment item
            play_action = QAction("Play Segment", self)
            play_action.setFont(FluentDesignSystem.get_font("body_medium"))
            play_action.triggered.connect(lambda: self.play_segment(data))
            menu.addAction(play_action)
            
            rename_speaker_action = QAction("Rename Speaker", self)
            rename_speaker_action.setFont(FluentDesignSystem.get_font("body_medium"))
            rename_speaker_action.triggered.connect(lambda: self.rename_speaker(data))
            menu.addAction(rename_speaker_action)
        elif isinstance(data, str) and ":" in data:
            # Word item
            play_action = QAction("Play Word", self)
            play_action.setFont(FluentDesignSystem.get_font("body_medium"))
            play_action.triggered.connect(lambda: self.play_word(data))
            menu.addAction(play_action)
            
        menu.exec(self.segments_tree.mapToGlobal(position))
        
    def show_text_context_menu(self, position):
        """Show context menu for text editor with Fluent Design."""
        menu = self.text_editor.createStandardContextMenu()
        menu.setFont(FluentDesignSystem.get_font("body_medium"))
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {FluentDesignSystem.get_theme_colors()["surface"].name()};
                border: 1px solid {FluentDesignSystem.get_theme_colors()["outline"].name()};
                border-radius: {FluentDesignSystem.get_border_radius("md")}px;
                padding: {FluentDesignSystem.get_spacing("sm")}px 0;
            }}
            
            QMenu::item {{
                padding: {FluentDesignSystem.get_spacing("sm")}px {FluentDesignSystem.get_spacing("lg")}px;
                color: {FluentDesignSystem.get_theme_colors()["on_surface"].name()};
            }}
            
            QMenu::item:selected {{
                background-color: {FluentDesignSystem.get_theme_colors()["secondary"].name()};
            }}
            
            QMenu::separator {{
                height: 1px;
                background: {FluentDesignSystem.get_theme_colors()["outline"].name()};
                margin: {FluentDesignSystem.get_spacing("sm")}px 0;
            }}
        """)
        
        # Add custom actions
        menu.addSeparator()
        
        play_action = QAction("Play Selection", self)
        play_action.setFont(FluentDesignSystem.get_font("body_medium"))
        play_action.triggered.connect(self.play_selection)
        menu.addAction(play_action)
        
        menu.exec(self.text_editor.mapToGlobal(position))
        
    def play_segment(self, segment_id: int):
        """
        Play a specific segment.
        
        Args:
            segment_id: ID of the segment to play
        """
        # In a full implementation, this would communicate with the audio player
        print(f"Playing segment {segment_id}")
        
    def play_word(self, word_data: str):
        """
        Play a specific word.
        
        Args:
            word_data: Data identifying the word to play
        """
        # In a full implementation, this would communicate with the audio player
        print(f"Playing word {word_data}")
        
    def play_selection(self):
        """Play the currently selected text."""
        # In a full implementation, this would communicate with the audio player
        print("Playing selection")
        
    def rename_speaker(self, segment_id: int):
        """
        Rename the speaker for a segment.
        
        Args:
            segment_id: ID of the segment to rename speaker for
        """
        # In a full implementation, this would show a dialog and update all segments
        # with the same speaker
        print(f"Renaming speaker for segment {segment_id}")
        
    def get_transcription_text(self) -> str:
        """
        Get the current transcription text.
        
        Returns:
            The transcription text
        """
        return self.text_editor.toPlainText()
        
    def export_srt(self, file_path: str):
        """
        Export transcription as SRT file.
        
        Args:
            file_path: Path to save the SRT file
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(self.segments, 1):
                    # Format timestamps
                    start_time = self.format_timestamp(segment.start_time)
                    end_time = self.format_timestamp(segment.end_time)
                    
                    # Write subtitle
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment.text}\n")
                    f.write("\n")
                    
            print(f"Transcription exported to {file_path}")
        except Exception as e:
            print(f"Error exporting SRT: {e}")
            
    def export_vtt(self, file_path: str):
        """
        Export transcription as VTT file.
        
        Args:
            file_path: Path to save the VTT file
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for i, segment in enumerate(self.segments, 1):
                    # Format timestamps
                    start_time = self.format_timestamp(segment.start_time, vtt_format=True)
                    end_time = self.format_timestamp(segment.end_time, vtt_format=True)
                    
                    # Write subtitle
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment.text}\n")
                    f.write("\n")
                    
            print(f"Transcription exported to {file_path}")
        except Exception as e:
            print(f"Error exporting VTT: {e}")
            
    def format_timestamp(self, seconds: float, vtt_format: bool = False) -> str:
        """
        Format timestamp in SRT or VTT format.
        
        Args:
            seconds: Time in seconds
            vtt_format: Whether to use VTT format (HH:MM:SS.mmm) or SRT (HH:MM:SS,mmm)
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        if vtt_format:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"