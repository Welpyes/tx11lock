import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import subprocess
import os
import tempfile
import sys
import yaml
from typing import Dict, Any

from widget_manager import WidgetManager

class LockScreen:
    def __init__(self, config_file: str = None):
        self.temp_dir = tempfile.mkdtemp()
        self.screenshot_path = os.path.join(self.temp_dir, "screenshot.png")
        self.blurred_path = os.path.join(self.temp_dir, "blurred.png")
        
        # Load configuration
        self.config = self.load_config(config_file)
        
        # Take screenshot and blur it
        self.capture_and_blur()
        
        # Create GTK window
        self.setup_window()
        
    def load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load configuration from YAML file or use defaults"""
        default_config = {
            'widgets': {
                'clock': {
                    'type': 'builtin.clock',
                    'class-name': 'clock-widget',
                    'options': {
                        'label': '%I:%M %p'
                    },
                    'position': 'center',
                    'offset_y': 0,
                    'offset_x': 0
                }
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f) or default_config
            except Exception as e:
                print(f"Error loading config file: {e}")
                return default_config
        
        return default_config
    
    def setup_css(self):
        """Setup CSS styling"""
        css_provider = Gtk.CssProvider()
        
        # Default CSS
        default_css = """
.clock-widget {
    font-size: 48px;
    font-weight: bold;
    color: white;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
    font-family: Sans;
}
"""
        
        # Try to load custom CSS file
        css_file = "lockscreen.css"
        if os.path.exists(css_file):
            try:
                css_provider.load_from_path(css_file)
            except Exception as e:
                print(f"Error loading CSS file: {e}")
                css_provider.load_from_data(default_css.encode())
        else:
            css_provider.load_from_data(default_css.encode())
        
        # Apply CSS to the screen
        display = Gdk.Display.get_default()
        screen = display.get_default_screen()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, 
            css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def capture_and_blur(self):
        """Take screenshot with scrot and blur with ffmpeg"""
        try:
            # Take screenshot with scrot
            subprocess.run([
                'scrot', 
                '--overwrite',
                self.screenshot_path
            ], check=True)
            
            # Blur the image with ffmpeg (acrylic-like effect)
            subprocess.run([
                'ffmpeg', 
                '-i', self.screenshot_path,
                '-vf', 'gblur=sigma=20',  # Gaussian blur with sigma=20
                '-y',  # Overwrite output file
                self.blurred_path
            ], check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            print(f"Error during screenshot/blur: {e}")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"Required command not found: {e}")
            print("Make sure 'scrot' and 'ffmpeg' are installed")
            sys.exit(1)
    
    def setup_window(self):
        """Setup GTK window with blurred background and widgets"""
        self.window = Gtk.Window()
        
        # Window properties
        self.window.set_title("Lockscreen")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.fullscreen()
        self.window.set_keep_above(True)
        self.window.set_modal(True)
        
        # Connect events
        self.window.connect('destroy', self.cleanup_and_quit)
        self.window.connect('key-press-event', self.on_key_press)
        
        # Create overlay container
        self.overlay = Gtk.Overlay()
        self.window.add(self.overlay)
        
        # Setup background image
        self.setup_background()
        
        # Setup CSS and widgets
        self.setup_css()
        self.widget_manager = WidgetManager(self.overlay)
        self.widget_manager.load_widgets(self.config)
        
        # Window focus and display
        self.window.set_can_focus(True)
        self.window.grab_focus()
        self.window.show_all()
        
        # Grab input
        Gdk.threads_add_idle(0, self.grab_input)
    
    def setup_background(self):
        """Setup the blurred background image"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.blurred_path)
            
            # Get screen size
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor()
            geometry = monitor.get_geometry()
            screen_width = geometry.width
            screen_height = geometry.height
            
            # Scale pixbuf to screen size
            scaled_pixbuf = pixbuf.scale_simple(
                screen_width, 
                screen_height, 
                GdkPixbuf.InterpType.BILINEAR
            )
            
            # Create and add background image
            background_image = Gtk.Image.new_from_pixbuf(scaled_pixbuf)
            self.overlay.add(background_image)
            
        except Exception as e:
            print(f"Error loading blurred image: {e}")
            sys.exit(1)
    
    def grab_input(self):
        """Grab keyboard input"""
        gdk_window = self.window.get_window()
        if gdk_window:
            Gdk.Device.grab(
                Gdk.Display.get_default().get_default_seat().get_keyboard(),
                gdk_window,
                Gdk.GrabOwnership.WINDOW,
                True,
                Gdk.EventMask.KEY_PRESS_MASK,
                None,
                Gdk.CURRENT_TIME
            )
        return False
    
    def on_key_press(self, widget, event):
        """Handle key press events"""
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ['space', 'Return', 'Escape']:
            self.cleanup_and_quit()
        return True
    
    def cleanup_and_quit(self, widget=None):
        """Clean up and quit"""
        try:
            if os.path.exists(self.screenshot_path):
                os.remove(self.screenshot_path)
            if os.path.exists(self.blurred_path):
                os.remove(self.blurred_path)
            os.rmdir(self.temp_dir)
        except OSError:
            pass
        
        Gtk.main_quit()
    
    def run(self):
        """Start the application"""
        Gtk.main()
