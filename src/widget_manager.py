import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Dict, Any, Optional

from widgets import BuiltinWidgets

class WidgetManager:
    """Manages widget creation and positioning"""
    
    def __init__(self, overlay: Gtk.Overlay, debug: bool = False):
        self.overlay = overlay
        self.widgets = {}
        self.debug = debug
    
    def debug_print(self, message: str):
        """Print debug message only if debug mode is enabled"""
        if self.debug:
            print(f"Debug - {message}")
    
    def create_widget(self, name: str, config: Dict[str, Any]) -> Optional[Any]:
        """Create a widget based on its configuration"""
        widget_type = config.get('type', '')
        
        # Check for custom class-name, otherwise use default
        css_class = config.get('class-name', f"{name}-widget")
        
        self.debug_print(f"Creating widget type: {widget_type}, css_class: {css_class}")
        
        if widget_type == 'builtin.clock':
            return BuiltinWidgets.Clock(config, css_class, debug=self.debug)
        elif widget_type == 'builtin.custom':
            self.debug_print("About to create BuiltinWidgets.Custom")
            widget_instance = BuiltinWidgets.Custom(config, css_class, debug=self.debug)
            self.debug_print("Created Custom widget successfully")
            return widget_instance
        else:
            print(f"Unknown widget type: {widget_type}")
            return None
    
    def position_widget(self, widget: Gtk.Widget, position: str, offset_x: int = 0, offset_y: int = 0):
        """Position a widget in the overlay"""
        # Create a box container for better control
        container = Gtk.Box()
        container.set_halign(Gtk.Align.FILL)
        container.set_valign(Gtk.Align.FILL)
        
        # Create another box to hold the widget with margins
        widget_box = Gtk.Box()
        widget_box.add(widget)
        
        # Parse position string
        position = position.lower()
        
        # Set horizontal alignment
        if 'west' in position:
            container.set_halign(Gtk.Align.START)
        elif 'east' in position:
            container.set_halign(Gtk.Align.END)
        else:
            container.set_halign(Gtk.Align.CENTER)
        
        # Set vertical alignment
        if 'north' in position:
            container.set_valign(Gtk.Align.START)
        elif 'south' in position:
            container.set_valign(Gtk.Align.END)
        else:
            container.set_valign(Gtk.Align.CENTER)
        
        # Apply offsets using margins on the widget box
        if offset_x > 0:
            widget_box.set_margin_left(offset_x)
        elif offset_x < 0:
            widget_box.set_margin_right(abs(offset_x))
            
        if offset_y > 0:
            widget_box.set_margin_top(offset_y)
        elif offset_y < 0:
            widget_box.set_margin_bottom(abs(offset_y))
        
        container.add(widget_box)
        return container
    
    def load_widgets(self, config: Dict[str, Any]):
        """Load widgets from configuration"""
        widgets_config = config.get('widgets', {})
        
        self.debug_print(f"Loading {len(widgets_config)} widgets")
        
        for name, widget_config in widgets_config.items():
            self.debug_print(f"Creating widget: {name}")
            
            # Create the widget
            widget_instance = self.create_widget(name, widget_config)
            if widget_instance is None:
                self.debug_print(f"Failed to create widget: {name}")
                continue
            
            # Get positioning info
            position = widget_config.get('position', 'center')
            offset_x = widget_config.get('offset_x', 0)
            offset_y = widget_config.get('offset_y', 0)
            
            self.debug_print(f"Positioning {name} at {position} with offset ({offset_x}, {offset_y})")
            
            # Get the widget container
            widget_container = widget_instance.get_widget()
            self.debug_print(f"Widget container type: {type(widget_container)}")
            
            # Position the widget
            positioned_widget = self.position_widget(
                widget_container, 
                position, 
                offset_x, 
                offset_y
            )
            
            # Add to overlay
            self.overlay.add_overlay(positioned_widget)
            positioned_widget.show_all()  # Ensure widget is visible
            self.widgets[name] = widget_instance
            
            self.debug_print(f"Successfully added widget {name} to overlay")
