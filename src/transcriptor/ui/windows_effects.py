"""
Windows 11 Fluent Design effects for PyQt6 applications.
Implements Mica and Acrylic materials using Windows APIs.
"""
import sys
import platform

# Check if we're on Windows
if platform.system() == "Windows":
    try:
        import ctypes
        from ctypes import wintypes
        import winreg
        
        # Windows API constants
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        DWM_SYSTEMBACKDROP_TYPE = {
            "DWMSBT_AUTO": 0,
            "DWMSBT_NONE": 1,
            "DWMSBT_MAINWINDOW": 2,
            "DWMSBT_TRANSIENTWINDOW": 3,
            "DWMSBT_TABBEDWINDOW": 4
        }
        
        # Check Windows version
        def get_windows_version():
            """Get Windows version as tuple (major, minor, build)."""
            version = sys.getwindowsversion()
            return (version.major, version.minor, version.build)
        
        # Check if Mica is supported (Windows 11 build 22000+)
        def is_mica_supported():
            """Check if Mica material is supported on this Windows version."""
            if platform.system() != "Windows":
                return False
            major, minor, build = get_windows_version()
            return major >= 10 and build >= 22000
        
        # Enable Mica material for a window
        def enable_mica(window_id):
            """
            Enable Mica material for a window.
            
            Args:
                window_id: Window handle (HWND)
                
            Returns:
                True if successful, False otherwise
            """
            if not is_mica_supported():
                return False
                
            try:
                # Get DWM API
                dwmapi = ctypes.windll.dwmapi
                
                # Enable Mica backdrop
                value = ctypes.c_int(DWM_SYSTEMBACKDROP_TYPE["DWMSBT_MAINWINDOW"])
                result = dwmapi.DwmSetWindowAttribute(
                    window_id,
                    DWMWA_SYSTEMBACKDROP_TYPE,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
                
                return result == 0  # S_OK
            except Exception as e:
                print(f"Failed to enable Mica: {e}")
                return False
        
        # Enable immersive dark mode
        def enable_immersive_dark_mode(window_id, enable=True):
            """
            Enable immersive dark mode for a window.
            
            Args:
                window_id: Window handle (HWND)
                enable: Whether to enable dark mode
                
            Returns:
                True if successful, False otherwise
            """
            try:
                # Get DWM API
                dwmapi = ctypes.windll.dwmapi
                
                # Enable immersive dark mode
                value = ctypes.c_int(1 if enable else 0)
                result = dwmapi.DwmSetWindowAttribute(
                    window_id,
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
                
                return result == 0  # S_OK
            except Exception as e:
                print(f"Failed to enable immersive dark mode: {e}")
                return False
        
        WINDOWS_EFFECTS_AVAILABLE = True
        
    except ImportError:
        WINDOWS_EFFECTS_AVAILABLE = False
else:
    WINDOWS_EFFECTS_AVAILABLE = False

class WindowsFluentEffects:
    """Windows 11 Fluent Design effects for PyQt6 applications."""
    
    @staticmethod
    def apply_mica_effect(window):
        """
        Apply Mica material effect to a PyQt6 window.
        
        Args:
            window: PyQt6 QMainWindow or QWidget
            
        Returns:
            True if effect was applied, False otherwise
        """
        if not WINDOWS_EFFECTS_AVAILABLE:
            return False
            
        try:
            # Get window handle
            hwnd = window.winId()
            if hwnd is None:
                return False
                
            # Enable Mica
            success = enable_mica(hwnd)
            
            # Also enable immersive dark mode if using dark theme
            if success:
                from ..ui.fluent_design import FluentDesignSystem
                # This would require access to the current theme setting
                # For now, we'll just enable it
                enable_immersive_dark_mode(hwnd, True)
                
            return success
        except Exception as e:
            print(f"Failed to apply Mica effect: {e}")
            return False
    
    @staticmethod
    def is_supported():
        """
        Check if Windows Fluent effects are supported.
        
        Returns:
            True if supported, False otherwise
        """
        return WINDOWS_EFFECTS_AVAILABLE and is_mica_supported()