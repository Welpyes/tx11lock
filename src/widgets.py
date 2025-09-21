import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from datetime import datetime
from typing import Dict, Any
import subprocess
import json
import re

class BuiltinWidgets:
    """Container for builtin widget classes"""
    
    class Clock:
        def __init__(self, config: Dict[str, Any], css_class: str, debug: bool = False):
            self.config = config
            self.css_class = css_class
            self.debug = debug
            self.label_format = config.get('options', {}).get('label', '%I:%M %p')
            
            # Create container with background support
            self.event_box, self.inner_box = self.create_widget_container(css_class)
            
            # Create GTK label
            self.widget = Gtk.Label()
            self.widget.get_style_context().add_class(f"{css_class}-text")
            
            # Add label to inner container (for proper padding)
            self.inner_box.pack_start(self.widget, True, True, 0)
            
            # Update immediately and start timer
            self.update_time()
            # Update every second
            GLib.timeout_add_seconds(1, self.update_time)
        
        def debug_print(self, message: str):
            """Print debug message only if debug mode is enabled"""
            if self.debug:
                print(f"Debug - Clock: {message}")
        
        def create_widget_container(self, css_class: str):
            """Create a container with background styling support"""
            # Create event box for background
            event_box = Gtk.EventBox()
            event_box.get_style_context().add_class(f"{css_class}-background")
            
            # Create inner box for padding - this is what handles spacing
            inner_box = Gtk.Box()
            inner_box.set_orientation(Gtk.Orientation.HORIZONTAL)
            inner_box.set_halign(Gtk.Align.CENTER)
            inner_box.set_valign(Gtk.Align.CENTER)
            inner_box.get_style_context().add_class(f"{css_class}-padding")
            
            event_box.add(inner_box)
            
            self.debug_print(f"Created container for {css_class}")
            return event_box, inner_box
        
        def update_time(self):
            """Update the time display"""
            current_time = datetime.now().strftime(self.label_format)
            self.widget.set_text(current_time)
            return True  # Continue the timer
        
        def get_widget(self):
            return self.event_box
    
    class Custom:
        def __init__(self, config: Dict[str, Any], css_class: str, debug: bool = False):
            self.config = config
            self.css_class = css_class
            self.debug = debug
            
            # Get configuration
            options = config.get('options', {})
            exec_options = config.get('exec_options', {})
            
            self.label_format = options.get('label', '')
            self.run_cmd = exec_options.get('run_cmd', '')
            self.run_interval = exec_options.get('run_interval', exec_options.get('interval', 300000))
            self.return_format = exec_options.get('return_format', 'text')
            
            self.debug_print(f"Creating container for {css_class}")
            # Create container with background support
            self.event_box, self.inner_box = self.create_widget_container(css_class)
            
            # Create GTK label
            self.widget = Gtk.Label()
            self.widget.get_style_context().add_class(f"{css_class}-text")
            
            # Add label to inner container (for proper padding)
            self.inner_box.pack_start(self.widget, True, True, 0)
            
            # Data storage
            self.last_data = {}
            
            # Update immediately and start timer
            self.update_data()
            # Convert milliseconds to seconds for GLib
            interval_seconds = max(1, self.run_interval // 1000)
            GLib.timeout_add_seconds(interval_seconds, self.update_data)
            
            self.debug_print(f"Custom widget initialization complete")
        
        def debug_print(self, message: str):
            """Print debug message only if debug mode is enabled"""
            if self.debug:
                print(f"Debug - Custom: {message}")
        
        def create_widget_container(self, css_class: str):
            """Create a container with background styling support"""
            # Create event box for background
            event_box = Gtk.EventBox()
            event_box.get_style_context().add_class(f"{css_class}-background")
            
            # Create inner box for padding - this is what handles spacing
            inner_box = Gtk.Box()
            inner_box.set_orientation(Gtk.Orientation.HORIZONTAL)
            inner_box.set_halign(Gtk.Align.CENTER)
            inner_box.set_valign(Gtk.Align.CENTER)
            inner_box.get_style_context().add_class(f"{css_class}-padding")
            
            event_box.add(inner_box)
            
            self.debug_print(f"Created container for {css_class}")
            return event_box, inner_box
        
        def get_nested_value(self, data: Dict, key_path: str) -> str:
            """Get nested dictionary value using dot notation like 'weather.main'
            Automatically uses first array element unless specific index is provided"""
            try:
                keys = key_path.split('.')
                value = data
                
                for key in keys:
                    # Handle explicit array indices
                    if key.isdigit():
                        value = value[int(key)]
                    else:
                        # Get the key value
                        value = value[key]
                        
                        # If the result is a list/array, automatically take the first element
                        # unless the next key is a digit (explicit index)
                        if isinstance(value, list) and len(value) > 0:
                            # Check if next key in the path is a digit (explicit index)
                            current_index = keys.index(key)
                            if current_index + 1 < len(keys) and keys[current_index + 1].isdigit():
                                # Next key is an explicit index, don't auto-select
                                pass
                            else:
                                # Auto-select first element
                                value = value[0]
                
                return str(value) if value is not None else ''
            except (KeyError, IndexError, TypeError):
                return f"{{ERROR: {key_path}}}"
        
        def format_label(self, data: Dict) -> str:
            """Format the label string with data substitution"""
            if not self.label_format:
                return str(data)
            
            formatted = self.label_format
            
            # Find all {key.path} patterns and replace them
            pattern = r'\{([^}]+)\}'
            matches = re.findall(pattern, formatted)
            
            for match in matches:
                # Handle special escape sequences first
                if match == 'n' or match == '\\n':
                    formatted = formatted.replace(f'{{{match}}}', '\n')
                else:
                    # Get the actual value from data
                    value = self.get_nested_value(data, match)
                    formatted = formatted.replace(f'{{{match}}}', value)
            
            # Handle literal \n in the string
            formatted = formatted.replace('\\n', '\n')
            
            return formatted
        
        def execute_command(self) -> str:
            """Execute the command and return output"""
            try:
                if not self.run_cmd:
                    return "No command specified"
                
                # Execute command
                result = subprocess.run(
                    self.run_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                if result.returncode != 0:
                    return f"Command failed: {result.stderr}"
                
                return result.stdout.strip()
                
            except subprocess.TimeoutExpired:
                return "Command timeout"
            except Exception as e:
                return f"Command error: {str(e)}"
        
        def update_data(self):
            """Update the data by executing command"""
            try:
                # Execute command
                output = self.execute_command()
                
                if self.return_format == 'json':
                    try:
                        # Parse JSON
                        data = json.loads(output)
                        self.last_data = data
                        
                        # Debug JSON structure
                        if self.debug:
                            self.debug_print(f"JSON keys at root: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                            if isinstance(data, dict) and 'current_condition' in data:
                                self.debug_print(f"current_condition type: {type(data['current_condition'])}")
                        
                        # Format and display
                        formatted_text = self.format_label(data)
                        self.widget.set_text(formatted_text)
                        
                    except json.JSONDecodeError as e:
                        error_msg = f"JSON Error: {str(e)}"
                        self.widget.set_text(error_msg)
                        if self.debug:
                            self.debug_print(f"JSON Parse Error: {e}")
                            self.debug_print(f"Raw output: {output[:500]}")
                else:
                    # Plain text mode
                    self.widget.set_text(output)
                    
            except Exception as e:
                error_msg = f"Update Error: {str(e)}"
                self.widget.set_text(error_msg)
                if self.debug:
                    self.debug_print(f"Update Error: {e}")
            
            return True  # Continue the timer
        
        def get_widget(self):
            return self.event_box
