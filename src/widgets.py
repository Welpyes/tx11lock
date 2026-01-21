import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from datetime import datetime
from typing import Dict, Any
import subprocess
import json
import re

class BuiltinWidgets:
    
    class Clock:
        def __init__(self, config: Dict[str, Any], css_class: str, debug: bool = False):
            self.config = config
            self.css_class = css_class
            self.debug = debug
            self.label_format = config.get('options', {}).get('label', '%I:%M %p')
            
            self.event_box, self.inner_box = self.create_widget_container(css_class)
            
            self.widget = Gtk.Label()
            self.widget.get_style_context().add_class(f"{css_class}-text")
            
            self.inner_box.pack_start(self.widget, True, True, 0)
            
            self.update_time()
            GLib.timeout_add_seconds(1, self.update_time)
        
        def debug_print(self, message: str):
            if self.debug:
                print(f"Debug - Clock: {message}")
        
        def create_widget_container(self, css_class: str):
            event_box = Gtk.EventBox()
            event_box.get_style_context().add_class(f"{css_class}-background")
            
            inner_box = Gtk.Box()
            inner_box.set_orientation(Gtk.Orientation.HORIZONTAL)
            inner_box.set_halign(Gtk.Align.CENTER)
            inner_box.set_valign(Gtk.Align.CENTER)
            inner_box.get_style_context().add_class(f"{css_class}-padding")
            
            event_box.add(inner_box)
            
            self.debug_print(f"Created container for {css_class}")
            return event_box, inner_box
        
        def update_time(self):
            current_time = datetime.now().strftime(self.label_format)
            self.widget.set_text(current_time)
            return True
        
        def get_widget(self):
            return self.event_box
    
    class Custom:
        def __init__(self, config: Dict[str, Any], css_class: str, debug: bool = False):
            self.config = config
            self.css_class = css_class
            self.debug = debug
            
            options = config.get('options', {})
            exec_options = config.get('exec_options', {})
            
            self.label_format = options.get('label', '')
            
            if 'commands' in exec_options:
                self.commands = exec_options.get('commands', {})
                self.run_cmd = None
                self.return_format = 'json'
            else:
                self.run_cmd = exec_options.get('run_cmd', '')
                self.return_format = exec_options.get('return_format', 'text')
                self.commands = None
            
            self.run_interval = exec_options.get('run_interval', exec_options.get('interval', 300000))
            
            self.debug_print(f"Creating container for {css_class}")
            self.event_box, self.inner_box = self.create_widget_container(css_class)
            
            self.widget = Gtk.Label()
            self.widget.get_style_context().add_class(f"{css_class}-text")
            
            self.inner_box.pack_start(self.widget, True, True, 0)
            
            self.last_data = {}
            
            self.update_data()
            interval_seconds = max(1, self.run_interval // 1000)
            GLib.timeout_add_seconds(interval_seconds, self.update_data)
            
            self.debug_print(f"Custom widget initialization complete")
        
        def debug_print(self, message: str):
            if self.debug:
                print(f"Debug - Custom: {message}")
        
        def create_widget_container(self, css_class: str):
            event_box = Gtk.EventBox()
            event_box.get_style_context().add_class(f"{css_class}-background")
            
            inner_box = Gtk.Box()
            inner_box.set_orientation(Gtk.Orientation.HORIZONTAL)
            inner_box.set_halign(Gtk.Align.CENTER)
            inner_box.set_valign(Gtk.Align.CENTER)
            inner_box.get_style_context().add_class(f"{css_class}-padding")
            
            event_box.add(inner_box)
            
            self.debug_print(f"Created container for {css_class}")
            return event_box, inner_box
        
        def get_nested_value(self, data: Dict, key_path: str) -> str:
            try:
                keys = key_path.split('.')
                value = data
                
                for i, key in enumerate(keys):
                    if key.isdigit():
                        value = value[int(key)]
                    else:
                        value = value[key]
                        
                        if isinstance(value, list) and len(value) > 0:
                            # Check if next key in the path is a digit (explicit index)
                            if i + 1 < len(keys) and keys[i + 1].isdigit():
                                pass
                            else:
                                value = value[0]
                
                return str(value) if value is not None else ''
            except (KeyError, IndexError, TypeError):
                return f"{{ERROR: {key_path}}}"
        
        def format_label(self, data: Dict) -> str:
            if not self.label_format:
                return str(data)
            
            formatted = self.label_format
            pattern = r'\{([^}]+)\}'
            matches = re.findall(pattern, formatted)
            
            for match in matches:
                if match == 'n' or match == '\\n':
                    formatted = formatted.replace(f'{{{match}}}', '\n')
                else:
                    value = self.get_nested_value(data, match)
                    formatted = formatted.replace(f'{{{match}}}', value)
            
            formatted = formatted.replace('\\n', '\n')
            return formatted
        
        def execute_command(self) -> str:
            try:
                if self.commands:
                    return self.execute_multiple_commands()
                else:
                    return self.execute_single_command()
            except Exception as e:
                return f"Command error: {str(e)}"
        
        def execute_single_command(self) -> str:
            if not self.run_cmd:
                return "No command specified"
            
            result = subprocess.run(
                self.run_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return f"Command failed: {result.stderr}"
            
            return result.stdout.strip()
        
        def execute_multiple_commands(self) -> str:
            combined_results = {}
            
            for cmd_name, cmd_config in self.commands.items():
                try:
                    run_cmd = cmd_config.get('run_cmd', '')
                    return_format = cmd_config.get('return_format', 'text')
                    
                    if not run_cmd:
                        combined_results[cmd_name] = f"No command specified for {cmd_name}"
                        continue
                    
                    self.debug_print(f"Executing command '{cmd_name}': {run_cmd}")
                    
                    result = subprocess.run(
                        run_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        combined_results[cmd_name] = f"Command failed: {result.stderr}"
                        continue
                    
                    output = result.stdout.strip()
                    
                    if return_format == 'json':
                        try:
                            parsed_data = json.loads(output)
                            combined_results[cmd_name] = parsed_data
                        except json.JSONDecodeError:
                            combined_results[cmd_name] = {"raw": output, "error": "Invalid JSON"}
                    else:
                        combined_results[cmd_name] = output
                
                except subprocess.TimeoutExpired:
                    combined_results[cmd_name] = f"Command timeout for {cmd_name}"
                except Exception as e:
                    combined_results[cmd_name] = f"Error in {cmd_name}: {str(e)}"
            
            return json.dumps(combined_results)
        
        def update_data(self):
            try:
                output = self.execute_command()
                
                if self.return_format == 'json':
                    try:
                        data = json.loads(output)
                        self.last_data = data
                        
                        if self.debug:
                            self.debug_print(f"JSON keys at root: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                            if isinstance(data, dict) and 'current_condition' in data:
                                self.debug_print(f"current_condition type: {type(data['current_condition'])}")
                        
                        formatted_text = self.format_label(data)
                        self.widget.set_text(formatted_text)
                        
                    except json.JSONDecodeError as e:
                        error_msg = f"JSON Error: {str(e)}"
                        self.widget.set_text(error_msg)
                        if self.debug:
                            self.debug_print(f"JSON Parse Error: {e}")
                            self.debug_print(f"Raw output: {output[:500]}")
                else:
                    self.widget.set_text(output)
                    
            except Exception as e:
                error_msg = f"Update Error: {str(e)}"
                self.widget.set_text(error_msg)
                if self.debug:
                    self.debug_print(f"Update Error: {e}")
            
            return True
        
        def get_widget(self):
            return self.event_box