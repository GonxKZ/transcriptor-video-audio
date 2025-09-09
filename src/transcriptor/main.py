import sys
import os
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow

def main():
    # Set application metadata
    QApplication.setApplicationName("Transcriptor")
    QApplication.setApplicationVersion("0.1.0")
    QApplication.setOrganizationName("Transcriptor Team")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
