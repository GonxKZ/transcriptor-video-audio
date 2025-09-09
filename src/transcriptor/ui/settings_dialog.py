"""
Settings dialog for configuring transcription parameters.
"""
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QFormLayout, QDialogButtonBox,
    QComboBox, QCheckBox, QLineEdit, QLabel
)

class SettingsDialog(QDialog):
    """Settings dialog to configure the transcription pipeline."""

    def __init__(self, current_settings: dict, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        
        self.settings = current_settings
        
        # Create widgets
        self.model_size_combo = QComboBox()
        self.model_size_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        
        self.compute_type_combo = QComboBox()
        self.compute_type_combo.addItems(["float16", "int8", "float32"])
        
        self.language_combo = QLineEdit(self.settings.get("language", "en"))
        
        self.diarization_checkbox = QCheckBox("Enable Speaker Diarization")
        
        self.hf_token_input = QLineEdit(self.settings.get("hf_token", ""))
        self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Layout
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        form_layout.addRow("Model Size:", self.model_size_combo)
        form_layout.addRow("Compute Type:", self.compute_type_combo)
        form_layout.addRow("Language (e.g., 'en', 'es'):", self.language_combo)
        form_layout.addRow(self.diarization_checkbox)
        form_layout.addRow("Hugging Face Token:", self.hf_token_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.load_settings()

    def load_settings(self):
        """Load current settings into the dialog widgets."""
        self.model_size_combo.setCurrentText(self.settings.get("model_size", "large-v3"))
        self.compute_type_combo.setCurrentText(self.settings.get("compute_type", "float16"))
        self.diarization_checkbox.setChecked(self.settings.get("diarization", True))

    def accept(self):
        """Save settings and close dialog."""
        self.settings["model_size"] = self.model_size_combo.currentText()
        self.settings["compute_type"] = self.compute_type_combo.currentText()
        self.settings["language"] = self.language_combo.text()
        self.settings["diarization"] = self.diarization_checkbox.isChecked()
        self.settings["hf_token"] = self.hf_token_input.text()
        super().accept()

    def get_settings(self) -> dict:
        """Return the updated settings."""
        return self.settings
