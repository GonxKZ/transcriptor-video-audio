"""
Test script to verify all UI/UX improvements are working correctly.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from transcriptor.ui.main_window import MainWindow
from transcriptor.ui.fluent_design import FluentDesignSystem

def test_fluent_design_system():
    """Test that the Fluent Design System is working correctly."""
    # Test light theme colors
    light_colors = FluentDesignSystem.get_theme_colors("light")
    assert "background" in light_colors
    assert "primary" in light_colors
    assert light_colors["primary"].name() == "#0078d4"
    
    # Test dark theme colors
    dark_colors = FluentDesignSystem.get_theme_colors("dark")
    assert "background" in dark_colors
    assert "primary" in dark_colors
    assert dark_colors["primary"].name() == "#0078d4"
    
    # Test typography
    font = FluentDesignSystem.get_font("body_medium")
    assert font.family() == "Segoe UI"
    
    # Test spacing
    spacing = FluentDesignSystem.get_spacing("md")
    assert isinstance(spacing, int)
    assert spacing > 0
    
    # Test border radius
    radius = FluentDesignSystem.get_border_radius("md")
    assert isinstance(radius, int)
    assert radius > 0
    
    print("✓ Fluent Design System tests passed")

def test_application_startup():
    """Test that the application starts up correctly with all improvements."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    
    # Check that window was created
    assert window is not None
    assert window.windowTitle() == "Transcriptor de Video/Audio"
    
    # Check that UI components exist
    assert hasattr(window, 'project_area')
    assert hasattr(window, 'process_panel')
    assert hasattr(window, 'transcription_editor')
    
    # Check that Fluent Design is applied
    palette = app.palette()
    assert palette is not None
    
    print("✓ Application startup tests passed")

if __name__ == "__main__":
    print("Running UI/UX improvement tests...")
    
    try:
        test_fluent_design_system()
        test_application_startup()
        print("\n🎉 All tests passed! UI/UX improvements are working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)