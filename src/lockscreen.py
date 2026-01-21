import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import subprocess
import os
import shutil
import tempfile
import sys
import yaml
import hashlib
import json
from typing import Dict, Any

from widget_manager import WidgetManager

class LockScreen:
    def __init__(self, config_file: str = None, debug: bool = False):
        self.debug = debug
        self.temp_dir = tempfile.mkdtemp()
        self.screenshot_path = os.path.join(self.temp_dir, "screenshot.png")
        self.bg_image_path = os.path.join(self.temp_dir, "background.png")
        
        if config_file:
            self.config_dir = os.path.dirname(os.path.abspath(config_file))
        else:
            self.config_dir = os.getcwd()
            
        self.config = self.load_config(config_file)
        self.prepare_background()
        self.setup_window()
        
    def load_config(self, config_file: str = None) -> Dict[str, Any]:
        default_config = {
            'background': {
                'screenshot': True,
                'path': '',
                'blur': True,
                'blur_radius': 20,
                'darken': 0.0
            },
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
        css_provider = Gtk.CssProvider()
        
        default_scss = """
.clock-widget {
    font-size: 48px;
    font-weight: bold;
    color: white;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
    font-family: Sans;
}

.weather-widget {
    font-family: Sans;
    font-size: 18px;
    color: white;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
}
"""
        
        scss_file = "lockscreen.scss"
        css_content = default_scss
        
        if os.path.exists(scss_file):
            try:
                css_content = self.compile_scss(scss_file)
            except Exception as e:
                print(f"Error compiling SCSS file: {e}")
                css_content = default_scss
        else:
            css_file = "lockscreen.css"
            if os.path.exists(css_file):
                try:
                    with open(css_file, 'r') as f:
                        css_content = f.read()
                except Exception as e:
                    print(f"Error loading CSS file: {e}")
                    css_content = default_scss
        
        try:
            css_provider.load_from_data(css_content.encode())
        except Exception as e:
            print(f"Error loading compiled CSS: {e}")
            css_provider.load_from_data(default_scss.encode())
        
        display = Gdk.Display.get_default()
        screen = display.get_default_screen()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, 
            css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def compile_scss(self, scss_file: str) -> str:
        try:
            import sass
            with open(scss_file, 'r') as f:
                scss_content = f.read()
            return sass.compile(string=scss_content)
        except ImportError:
            print("Warning: libsass not installed. Install with: pip install libsass")
            print("Falling back to treating SCSS as CSS...")
            with open(scss_file, 'r') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"SCSS compilation failed: {e}")
    
    def prepare_background(self):
        bg_config = self.config.get('background', {})
        is_screenshot = bg_config.get('screenshot', True)
        if 'mode' in bg_config and 'screenshot' not in bg_config:
            is_screenshot = (bg_config['mode'] == 'screenshot')
            
        custom_path = bg_config.get('path', '')
        should_blur = bg_config.get('blur', True)
        blur_radius = bg_config.get('blur_radius', bg_config.get('blur_sigma', 20))
        darken_factor = float(bg_config.get('darken', 0.0))
        
        cache_dir = os.path.expanduser("~/.cache/tx11lock")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        cache_file = os.path.join(cache_dir, "bg.png")
        state_file = os.path.join(cache_dir, "state.json")
        
        source_path = ""
        if not is_screenshot:
            if custom_path:
                expanded_path = os.path.expanduser(custom_path)
                if not os.path.isabs(expanded_path):
                    abs_path = os.path.join(self.config_dir, expanded_path)
                    if os.path.exists(abs_path):
                        expanded_path = abs_path
                
                if os.path.exists(expanded_path):
                    source_path = expanded_path
                else:
                    print(f"Warning: Background image not found at '{custom_path}'. Falling back to screenshot.")
                    is_screenshot = True
            else:
                is_screenshot = True

        current_state = {
            'screenshot': is_screenshot,
            'path': source_path,
            'blur': should_blur,
            'blur_radius': blur_radius,
            'darken': darken_factor
        }
        
        if not is_screenshot and source_path:
            try:
                current_state['mtime'] = os.path.getmtime(source_path)
            except OSError:
                pass
        
        use_cache = False
        if not is_screenshot and os.path.exists(cache_file) and os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    saved_state = json.load(f)
                if saved_state == current_state:
                    use_cache = True
            except Exception:
                pass
                
        if use_cache:
            if self.debug:
                print("Using cached background")
            self.bg_image_path = cache_file
            return

        if is_screenshot:
            source_path = self.screenshot_path
            try:
                subprocess.run(['scrot', '--overwrite', source_path], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error taking screenshot: {e}")
                sys.exit(1)
        
        filters = []
        if should_blur:
            filters.append(f'gblur=sigma={blur_radius}')
        if darken_factor > 0:
            val = max(0.0, min(1.0, darken_factor))
            filters.append(f'eq=brightness=-{val}')
            
        output_path = cache_file if not is_screenshot else self.bg_image_path
        
        try:
            if filters:
                subprocess.run([
                    'ffmpeg', 
                    '-i', source_path,
                    '-vf', ','.join(filters),
                    '-y',
                    output_path
                ], check=True, capture_output=True)
            else:
                shutil.copy2(source_path, output_path)
            
            if not is_screenshot:
                with open(state_file, 'w') as f:
                    json.dump(current_state, f)
                self.bg_image_path = output_path
                
        except subprocess.CalledProcessError as e:
            print(f"Error processing background: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error preparing background: {e}")
            sys.exit(1)
    
    def setup_window(self):
        self.window = Gtk.Window()
        self.window.set_title("Lockscreen")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.fullscreen()
        self.window.set_keep_above(True)
        self.window.set_modal(True)
        self.window.stick()
        
        self.window.connect('destroy', self.cleanup_and_quit)
        self.window.connect('key-press-event', self.on_key_press)
        
        self.overlay = Gtk.Overlay()
        self.window.add(self.overlay)
        
        self.setup_background()
        self.setup_css()
        self.widget_manager = WidgetManager(self.overlay, debug=self.debug)
        self.widget_manager.load_widgets(self.config)
        
        self.window.set_can_focus(True)
        self.window.grab_focus()
        self.window.show_all()
        
        Gdk.threads_add_idle(0, self.grab_input)
    
    def setup_background(self):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.bg_image_path)
            
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor()
            geometry = monitor.get_geometry()
            screen_width = geometry.width
            screen_height = geometry.height
            
            img_w = pixbuf.get_width()
            img_h = pixbuf.get_height()
            
            ratio_w = screen_width / img_w
            ratio_h = screen_height / img_h
            scale = max(ratio_w, ratio_h)
            
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            scaled_pixbuf = pixbuf.scale_simple(
                new_w, 
                new_h, 
                GdkPixbuf.InterpType.BILINEAR
            )
            
            x_offset = (new_w - screen_width) // 2
            y_offset = (new_h - screen_height) // 2
            
            final_pixbuf = scaled_pixbuf.new_subpixbuf(
                x_offset, 
                y_offset, 
                screen_width, 
                screen_height
            )
            
            background_image = Gtk.Image.new_from_pixbuf(final_pixbuf)
            self.overlay.add(background_image)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            sys.exit(1)
    
    def grab_input(self):
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
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ['space', 'Return', 'Escape']:
            self.cleanup_and_quit()
        return True
    
    def cleanup_and_quit(self, widget=None):
        try:
            if os.path.exists(self.screenshot_path):
                os.remove(self.screenshot_path)
            if os.path.exists(self.bg_image_path):
                os.remove(self.bg_image_path)
            os.rmdir(self.temp_dir)
        except OSError:
            pass
        
        Gtk.main_quit()
    
    def run(self):
        Gtk.main()