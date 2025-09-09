"""
Fluent Design System for Transcriptor application.
Contains color schemes, typography, and visual elements following Windows 11 Fluent Design principles.
"""
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

class FluentDesignSystem:
    """Fluent Design System implementation for the Transcriptor application."""
    
    # Windows 11 Fluent Design Colors
    # Based on Microsoft's design guidelines
    COLORS = {
        # Light Theme
        "light": {
            "background": QColor(243, 243, 243),  # #F3F3F3
            "surface": QColor(255, 255, 255),     # #FFFFFF
            "surface_variant": QColor(249, 249, 249),  # #F9F9F9
            "primary": QColor(0, 120, 212),       # #0078D4 (Windows blue)
            "primary_hover": QColor(16, 110, 190),  # #106EBE
            "primary_pressed": QColor(0, 90, 158),  # #005A9E
            "secondary": QColor(240, 240, 240),   # #F0F0F0
            "on_surface": QColor(0, 0, 0),        # #000000
            "on_surface_variant": QColor(96, 96, 96),  # #606060
            "outline": QColor(214, 214, 214),     # #D6D6D6
            "error": QColor(196, 43, 28),         # #C42B1C
            "success": QColor(17, 128, 52),       # #118034
            "warning": QColor(218, 165, 32),      # #DAA520
        },
        
        # Dark Theme
        "dark": {
            "background": QColor(32, 32, 32),     # #202020
            "surface": QColor(40, 40, 40),        # #282828
            "surface_variant": QColor(45, 45, 45),  # #2D2D2D
            "primary": QColor(0, 120, 212),       # #0078D4 (Windows blue)
            "primary_hover": QColor(30, 140, 220),  # #1E8CD8
            "primary_pressed": QColor(50, 160, 230),  # #32A0E6
            "secondary": QColor(50, 50, 50),      # #323232
            "on_surface": QColor(255, 255, 255),  # #FFFFFF
            "on_surface_variant": QColor(200, 200, 200),  # #C8C8C8
            "outline": QColor(68, 68, 68),        # #444444
            "error": QColor(255, 117, 102),       # #FF7566
            "success": QColor(60, 180, 90),       # #3CB45A
            "warning": QColor(230, 190, 70),      # #E6BE46
        }
    }
    
    # Typography
    TYPOGRAPHY = {
        "display": QFont("Segoe UI", 28, QFont.Weight.Light),
        "title_large": QFont("Segoe UI", 20, QFont.Weight.DemiBold),
        "title_medium": QFont("Segoe UI", 16, QFont.Weight.DemiBold),
        "title_small": QFont("Segoe UI", 14, QFont.Weight.DemiBold),
        "body_large": QFont("Segoe UI", 14, QFont.Weight.Normal),
        "body_medium": QFont("Segoe UI", 12, QFont.Weight.Normal),
        "body_small": QFont("Segoe UI", 10, QFont.Weight.Normal),
        "caption": QFont("Segoe UI", 10, QFont.Weight.Normal),
        "button": QFont("Segoe UI", 14, QFont.Weight.DemiBold),
    }
    
    # Spacing scale (in pixels)
    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 12,
        "lg": 16,
        "xl": 24,
        "xxl": 32,
        "xxxl": 48
    }
    
    # Border radius
    BORDER_RADIUS = {
        "sm": 4,
        "md": 8,
        "lg": 12,
        "xl": 16,
        "circle": 999
    }
    
    # Elevation (shadows)
    ELEVATION = {
        "level0": "0px 0px 0px rgba(0, 0, 0, 0)",
        "level1": "0px 2px 4px rgba(0, 0, 0, 0.1)",
        "level2": "0px 4px 8px rgba(0, 0, 0, 0.15)",
        "level3": "0px 8px 16px rgba(0, 0, 0, 0.2)",
        "level4": "0px 12px 24px rgba(0, 0, 0, 0.25)"
    }
    
    @classmethod
    def get_theme_colors(cls, theme="light"):
        """
        Get color scheme for the specified theme.
        
        Args:
            theme: Theme name ("light" or "dark")
            
        Returns:
            Dictionary of colors for the theme
        """
        return cls.COLORS.get(theme, cls.COLORS["light"])
    
    @classmethod
    def get_font(cls, style="body_medium"):
        """
        Get font for the specified style.
        
        Args:
            style: Font style name
            
        Returns:
            QFont object
        """
        return cls.TYPOGRAPHY.get(style, cls.TYPOGRAPHY["body_medium"])
    
    @classmethod
    def get_spacing(cls, size="md"):
        """
        Get spacing value for the specified size.
        
        Args:
            size: Spacing size name
            
        Returns:
            Spacing value in pixels
        """
        return cls.SPACING.get(size, cls.SPACING["md"])
    
    @classmethod
    def get_border_radius(cls, size="md"):
        """
        Get border radius for the specified size.
        
        Args:
            size: Border radius size name
            
        Returns:
            Border radius value in pixels
        """
        return cls.BORDER_RADIUS.get(size, cls.BORDER_RADIUS["md"])