#!/usr/bin/env python3

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
import gi
import dbus

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

class BlurredScreenOverlay:
    def __init__(self):
        self.window = None
        self.temp_dir = self.get_temp_dir()
        self.time_label = None
        self.date_label = None
        self.music_info = {"title": "No song playing", "artist": "", "art_url": None, "playback_status": "Stopped"}
        self.media_player = None
        self.text_font = self.detect_text_font()
        self.icon_font = self.detect_icon_font()
        self.weather_data = None
        self.uptime_info = ""
        self.weather_cache_file = os.path.expanduser("~/.cache/pylocksc/weather.json")
        
        # Ensure cache directory exists
        cache_dir = os.path.dirname(self.weather_cache_file)
        os.makedirs(cache_dir, exist_ok=True)
        
    def detect_text_font(self):
        """Detect available Japanese font using fc-list"""
        try:
            # Run fc-list to get available fonts
            result = subprocess.run(['fc-list', ':lang=ja', 'family'], 
                                  capture_output=True, text=True, check=True)
            fonts = result.stdout.strip().split('\n')
            
            # Preferred fonts in order
            preferred_fonts = [
                "Noto Sans CJK JP",
                "Noto Sans CJK",
                "Noto CJK JP",
                "DejaVu Sans",
                "Liberation Sans"
            ]
            
            # Check each preferred font against available fonts
            for preferred in preferred_fonts:
                for font_line in fonts:
                    if preferred.lower() in font_line.lower():
                        # Extract the font family name (first part before comma if multiple)
                        font_name = font_line.split(',')[0].strip()
                        return font_name
            
            # If no Japanese font found, try general CJK fonts
            result2 = subprocess.run(['fc-list', ':lang=zh', 'family'], 
                                   capture_output=True, text=True, check=True)
            cjk_fonts = result2.stdout.strip().split('\n')
            
            for font_line in cjk_fonts:
                if 'noto' in font_line.lower() and 'cjk' in font_line.lower():
                    font_name = font_line.split(',')[0].strip()
                    return font_name
                    
            return "Sans"  # Final fallback
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback if fc-list not available
            return "Noto Sans CJK JP"
    
    def detect_icon_font(self):
        """Detect available Nerd Font using fc-list"""
        try:
            # Run fc-list to get all monospace fonts
            result = subprocess.run(['fc-list', ':spacing=mono', 'family'], 
                                  capture_output=True, text=True, check=True)
            fonts = result.stdout.strip().split('\n')
            
            # Preferred icon fonts
            preferred_fonts = [
                "Cousine Nerd Font Mono",
                "Cousine NF",
                "FiraCode Nerd Font Mono", 
                "FiraCode NF",
                "JetBrainsMono Nerd Font Mono",
                "JetBrainsMono NF",
                "Hack Nerd Font Mono",
                "Hack NF",
                "DejaVu Sans Mono"
            ]
            
            # Check each preferred font against available fonts
            for preferred in preferred_fonts:
                for font_line in fonts:
                    if preferred.lower() in font_line.lower():
                        # Extract the font family name
                        font_name = font_line.split(',')[0].strip()
                        return font_name
            
            # Try a broader search for any Nerd Font
            for font_line in fonts:
                if 'nerd font' in font_line.lower() or ' nf' in font_line.lower():
                    font_name = font_line.split(',')[0].strip()
                    return font_name
                    
            return "monospace"  # Final fallback
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback if fc-list not available
            return "Cousine Nerd Font Mono"
    
    def get_temp_dir(self):
        """Get temporary directory, preferring $TMPDIR over /tmp"""
        tmpdir = os.environ.get('TMPDIR')
        if tmpdir and os.path.isdir(tmpdir):
            return tmpdir
        return '/tmp'
    
    def check_dependencies(self):
        """Check if required tools are available"""
        tools = ['scrot', 'ffmpeg']
        missing = []
        
        for tool in tools:
            try:
                subprocess.run(['which', tool], check=True, 
                             capture_output=True, text=True)
            except subprocess.CalledProcessError:
                missing.append(tool)
        
        if missing:
            print(f"Error: Missing required tools: {', '.join(missing)}")
            print("Please install them:")
            for tool in missing:
                if tool == 'scrot':
                    print("  - Ubuntu/Debian: sudo apt install scrot")
                    print("  - Fedora: sudo dnf install scrot")
                    print("  - Arch: sudo pacman -S scrot")
                elif tool == 'ffmpeg':
                    print("  - Ubuntu/Debian: sudo apt install ffmpeg")
                    print("  - Fedora: sudo dnf install ffmpeg")
                    print("  - Arch: sudo pacman -S ffmpeg")
            return False
        return True
    
    def take_screenshot(self):
        """Take a screenshot using scrot"""
        screenshot_path = os.path.join(self.temp_dir, 'screenshot.png')
        
        try:
            # Use scrot to take screenshot
            subprocess.run(['scrot', screenshot_path], check=True)
            return screenshot_path
        except subprocess.CalledProcessError as e:
            print(f"Error taking screenshot: {e}")
            return None
    
    def media_control_action(self, action):
        """Execute media control action via D-Bus"""
        if not self.media_player:
            return
            
        try:
            if action == "previous":
                self.media_player.Previous()
            elif action == "playpause":
                self.media_player.PlayPause()
            elif action == "next":
                self.media_player.Next()
        except Exception as e:
            print(f"Error executing media control action: {e}")
    
    def on_media_control_click(self, widget, event):
        """Handle clicks on media control buttons"""
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        
        # Calculate control area (bottom part of right section)
        left_width = width * 0.4
        right_width = width * 0.6
        control_y_start = height * 0.75
        
        # Check if click is in the control area
        if (event.x > left_width and 
            event.y > control_y_start):
            
            # Calculate button positions
            control_start_x = left_width + (right_width * 0.05)
            button_spacing = right_width * 0.25
            button_width = right_width * 0.2  # Define button click area width
            
            prev_x = control_start_x
            play_x = control_start_x + button_spacing
            next_x = control_start_x + (button_spacing * 2)
            
            # Determine which button was clicked (with more generous click areas)
            if prev_x <= event.x < prev_x + button_width:
                print("Previous button clicked")
                self.media_control_action("previous")
            elif play_x <= event.x < play_x + button_width:
                print("Play/Pause button clicked")
                self.media_control_action("playpause")
            elif next_x <= event.x < next_x + button_width:
                print("Next button clicked")
                self.media_control_action("next")
                
        return True  # Consume the event
    
    def blur_image(self, input_path):
        """Blur the image heavily using ffmpeg with gaussian blur"""
        output_path = os.path.join(self.temp_dir, 'blurred_screenshot.png')
        
        try:
            # Apply heavy gaussian blur using ffmpeg
            # Using gblur for better gaussian blur (sigma of 20)
            cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-vf', 'gblur=sigma=20',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error blurring image: {e}")
            return None
    
    def create_fullscreen_window(self, image_path):
        """Create and show fullscreen window with blurred image"""
        self.window = Gtk.Window()
        self.window.set_title("Blurred Screen Overlay")
        
        # Make window fullscreen
        self.window.fullscreen()
        
        # Set window properties
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_keep_above(True)
        
        # Load and display the blurred image
        try:
            # Get screen dimensions
            screen = Gdk.Screen.get_default()
            screen_width = screen.get_width()
            screen_height = screen.get_height()
            
            # Load the image and scale it to screen size
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            scaled_pixbuf = pixbuf.scale_simple(
                screen_width, screen_height, GdkPixbuf.InterpType.BILINEAR
            )
            
            # Create image widget
            image = Gtk.Image.new_from_pixbuf(scaled_pixbuf)
            
            # Create an overlay to add time/date
            overlay = Gtk.Overlay()
            overlay.add(image)
            
            # Create a vertical box for time and date (offset upwards by 10%)
            time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            time_box.set_halign(Gtk.Align.CENTER)
            time_box.set_valign(Gtk.Align.CENTER)
            time_box.set_margin_bottom(int(screen_height * 0.1))  # Offset upwards by 10%
            
            # Time label (big)
            self.time_label = Gtk.Label()
            self.time_label.set_halign(Gtk.Align.CENTER)
            time_box.pack_start(self.time_label, False, False, 0)
            
            # Date label (small)
            self.date_label = Gtk.Label()
            self.date_label.set_halign(Gtk.Align.CENTER)
            time_box.pack_start(self.date_label, False, False, 0)
            
            overlay.add_overlay(time_box)
            
            # Create weather widget at bottom left
            weather_widget = Gtk.DrawingArea()
            weather_widget.set_size_request(
                int(screen_width * 0.15),  # 15% of screen width
                int(screen_height * 0.12)  # 12% of screen height
            )
            weather_widget.set_halign(Gtk.Align.START)
            weather_widget.set_valign(Gtk.Align.END)
            weather_widget.set_margin_left(20)
            weather_widget.set_margin_bottom(20)
            weather_widget.connect('draw', self.draw_weather_widget)
            
            overlay.add_overlay(weather_widget)
            
            # Create uptime widget at bottom right
            uptime_widget = Gtk.DrawingArea()
            uptime_widget.set_size_request(
                int(screen_width * 0.18),  # 18% of screen width (increased from 12%)
                int(screen_height * 0.06)  # 6% of screen height
            )
            uptime_widget.set_halign(Gtk.Align.END)
            uptime_widget.set_valign(Gtk.Align.END)
            uptime_widget.set_margin_right(20)
            uptime_widget.set_margin_bottom(20)
            uptime_widget.connect('draw', self.draw_uptime_widget)
            
            overlay.add_overlay(uptime_widget)
            
            # Create gray rectangle widget at bottom (20% width, 15% height)
            bottom_widget = Gtk.DrawingArea()
            bottom_widget.set_size_request(
                int(screen_width * 0.2),  # 20% of screen width
                int(screen_height * 0.15)  # 15% of screen height (less square)
            )
            bottom_widget.set_halign(Gtk.Align.CENTER)
            bottom_widget.set_valign(Gtk.Align.END)
            bottom_widget.connect('draw', self.draw_gray_rectangle)
            
            overlay.add_overlay(bottom_widget)
            
            self.window.add(overlay)
            
            # Update time immediately and start timer
            self.update_time()
            self.update_music_info()
            self.update_weather()
            self.update_uptime()
            GLib.timeout_add(1000, self.update_time)  # Update every second
            GLib.timeout_add(5000, self.update_music_info)  # Update music info every 5 seconds
            GLib.timeout_add(300000, self.update_weather)  # Update weather every 5 minutes
            GLib.timeout_add(10000, self.update_uptime)  # Update uptime every 10 seconds
            
        except Exception as e:
            print(f"Error loading image: {e}")
            # Fallback to a simple colored window
            self.window.override_background_color(
                Gtk.StateFlags.NORMAL, 
                Gdk.RGBA(0.2, 0.2, 0.2, 0.8)
            )
        
        # Connect events (disable click-to-exit on main window)
        self.window.connect('destroy', Gtk.main_quit)
        self.window.connect('key-press-event', self.on_key_press)
        # Remove button-press-event from main window to allow media controls
        
        # Make window focusable
        self.window.set_can_focus(True)
        self.window.set_events(Gdk.EventMask.KEY_PRESS_MASK | 
                              Gdk.EventMask.BUTTON_PRESS_MASK)
        
        self.window.show_all()
        self.window.grab_focus()
    
    def draw_gray_rectangle(self, widget, cr):
        """Draw a rounded gray rectangle with music info and album art"""
        import math
        
        # Get widget dimensions
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        
        # Corner radius for rounded rectangle
        radius = min(width, height) * 0.1
        
        # Draw main rounded rectangle background
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.4)  # More transparent (0.4 instead of 0.8)
        
        # Create rounded rectangle path
        cr.arc(radius, radius, radius, math.pi, 3 * math.pi / 2)
        cr.arc(width - radius, radius, radius, 3 * math.pi / 2, 0)
        cr.arc(width - radius, height - radius, radius, 0, math.pi / 2)
        cr.arc(radius, height - radius, radius, math.pi / 2, math.pi)
        cr.close_path()
        cr.fill()
        
        # Calculate sections
        left_width = width * 0.4   # 40% for left side
        right_width = width * 0.6  # 60% for right side
        
        # Left side - album art or rounded square
        square_size = min(left_width * 0.7, height * 0.7)  # 70% of available space
        square_x = (left_width - square_size) / 2
        square_y = (height - square_size) / 2
        square_radius = square_size * 0.15
        
        # Try to load album art
        album_art = self.load_album_art(self.music_info.get("art_url"), int(square_size))
        
        if album_art:
            # Save current state
            cr.save()
            
            # Create clipping path for rounded corners
            cr.arc(square_x + square_radius, square_y + square_radius, square_radius, math.pi, 3 * math.pi / 2)
            cr.arc(square_x + square_size - square_radius, square_y + square_radius, square_radius, 3 * math.pi / 2, 0)
            cr.arc(square_x + square_size - square_radius, square_y + square_size - square_radius, square_radius, 0, math.pi / 2)
            cr.arc(square_x + square_radius, square_y + square_size - square_radius, square_radius, math.pi / 2, math.pi)
            cr.close_path()
            cr.clip()
            
            # Draw album art
            Gdk.cairo_set_source_pixbuf(cr, album_art, square_x, square_y)
            cr.paint()
            
            # Restore state
            cr.restore()
        else:
            # Fallback: draw rounded square
            cr.set_source_rgba(0.7, 0.7, 0.7, 0.6)  # Lighter gray for the square
            
            cr.arc(square_x + square_radius, square_y + square_radius, square_radius, math.pi, 3 * math.pi / 2)
            cr.arc(square_x + square_size - square_radius, square_y + square_radius, square_radius, 3 * math.pi / 2, 0)
            cr.arc(square_x + square_size - square_radius, square_y + square_size - square_radius, square_radius, 0, math.pi / 2)
            cr.arc(square_x + square_radius, square_y + square_size - square_radius, square_radius, math.pi / 2, math.pi)
            cr.close_path()
            cr.fill()
        
        # Right side - music info (title and artist on separate lines)
        title = self.music_info.get("title", "No song playing")
        artist = self.music_info.get("artist", "")
        playback_status = self.music_info.get("playback_status", "Stopped")
        
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)  # White text
        cr.select_font_face(self.text_font, 0, 0)  # Use detected font
        
        # Title font size (larger)
        title_font_size = height * 0.11
        cr.set_font_size(title_font_size)
        
        # Calculate text positioning
        text_start_x = left_width + (right_width * 0.05)  # Small left margin in right section
        text_width = right_width * 0.9  # Available width for text
        
        # Draw title
        title_extents = cr.text_extents(title)
        if title_extents.width > text_width:
            # Truncate title if too long
            while title_extents.width > text_width and len(title) > 3:
                title = title[:-4] + "..."
                title_extents = cr.text_extents(title)
        
        title_y = height * 0.35  # Position title in upper part of right section
        cr.move_to(text_start_x, title_y)
        cr.show_text(title)
        
        # Artist font size (smaller)
        if artist:
            artist_font_size = height * 0.08
            cr.set_font_size(artist_font_size)
            
            artist_extents = cr.text_extents(artist)
            if artist_extents.width > text_width:
                # Truncate artist if too long
                while artist_extents.width > text_width and len(artist) > 3:
                    artist = artist[:-4] + "..."
                    artist_extents = cr.text_extents(artist)
            
            artist_y = height * 0.55  # Position artist closer to title
            cr.move_to(text_start_x, artist_y)
            cr.show_text(artist)
        
        # Media controls (Previous, Play/Pause, Next)
        if self.music_info.get("title") != "No song playing":
            # Switch to icon font for media controls
            cr.select_font_face(self.icon_font, 0, 0)
            control_font_size = height * 0.12
            cr.set_font_size(control_font_size)
            
            # Media control icons
            prev_icon = "󰒮"  # Previous
            play_icon = "󰐎" if playback_status == "Playing" else "󰐊"  # Play/Pause
            next_icon = "󰒭"  # Next
            
            control_y = height * 0.8  # Position controls at bottom
            control_start_x = text_start_x
            button_spacing = right_width * 0.25
            
            # Draw previous button
            cr.move_to(control_start_x, control_y)
            cr.show_text(prev_icon)
            
            # Draw play/pause button
            cr.move_to(control_start_x + button_spacing, control_y)
            cr.show_text(play_icon)
            
            # Draw next button
            cr.move_to(control_start_x + (button_spacing * 2), control_y)
            cr.show_text(next_icon)
        
        return False
    
    def draw_weather_widget(self, widget, cr):
        """Draw weather information widget"""
        import math
        
        # Get widget dimensions
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        
        # Corner radius for rounded rectangle
        radius = min(width, height) * 0.1
        
        # Draw transparent background (no visible box)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)  # Fully transparent
        
        # Create rounded rectangle path (for potential future use)
        cr.arc(radius, radius, radius, math.pi, 3 * math.pi / 2)
        cr.arc(width - radius, radius, radius, 3 * math.pi / 2, 0)
        cr.arc(width - radius, height - radius, radius, 0, math.pi / 2)
        cr.arc(radius, height - radius, radius, math.pi / 2, math.pi)
        cr.close_path()
        cr.fill()
        
        # Draw weather information
        if self.weather_data:
            try:
                current = self.weather_data['current_condition'][0]
                
                # Weather description
                weather_desc = current['weatherDesc'][0]['value']
                temp = current['temp_C'] + "°C"
                wind = current['windspeedKmph'] + " km/h"
                humidity = current['humidity'] + "%"
                
                # Set font and color
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)  # White text
                cr.select_font_face(self.text_font, 0, 0)
                
                # Font sizes
                desc_font_size = height * 0.16
                data_font_size = height * 0.13
                
                margin = width * 0.05
                line_height = height * 0.22
                
                # Draw weather description
                cr.set_font_size(desc_font_size)
                cr.move_to(margin, line_height)
                cr.show_text(weather_desc)
                
                # Draw temperature
                cr.set_font_size(data_font_size)
                cr.move_to(margin, line_height * 2)
                cr.show_text(temp)
                
                # Draw wind speed
                cr.move_to(margin, line_height * 3)
                cr.show_text(wind)
                
                # Draw humidity
                cr.move_to(margin, line_height * 4)
                cr.show_text(humidity)
                
            except (KeyError, IndexError):
                # Error parsing weather data
                cr.set_source_rgba(1.0, 0.5, 0.5, 0.9)  # Light red
                cr.select_font_face(self.text_font, 0, 0)
                cr.set_font_size(height * 0.15)
                cr.move_to(width * 0.05, height * 0.5)
                cr.show_text("Weather data error")
        else:
            # No weather data available
            cr.set_source_rgba(0.8, 0.8, 0.8, 0.9)  # Light gray
            cr.select_font_face(self.text_font, 0, 0)
            cr.set_font_size(height * 0.15)
            cr.move_to(width * 0.05, height * 0.5)
            cr.show_text("Weather unavailable")
        
        return False
    
    def draw_uptime_widget(self, widget, cr):
        """Draw uptime information widget"""
        import math
        
        # Get widget dimensions
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        
        # Corner radius for rounded rectangle
        radius = min(width, height) * 0.1
        
        # Draw transparent background (no visible box)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)  # Fully transparent
        
        # Create rounded rectangle path (for potential future use)
        cr.arc(radius, radius, radius, math.pi, 3 * math.pi / 2)
        cr.arc(width - radius, radius, radius, 3 * math.pi / 2, 0)
        cr.arc(width - radius, height - radius, radius, 0, math.pi / 2)
        cr.arc(radius, height - radius, radius, math.pi / 2, math.pi)
        cr.close_path()
        cr.fill()
        
        # Draw uptime information
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)  # White text
        cr.select_font_face(self.text_font, 0, 0)
        
        # Start with smaller font and adjust if needed
        font_size = height * 0.25
        cr.set_font_size(font_size)
        
        # Clean up uptime text
        uptime_text = self.uptime_info.replace("up ", "").replace("up", "")
        
        # Check if text fits, if not reduce font size
        text_extents = cr.text_extents(uptime_text)
        while text_extents.width > width * 0.95 and font_size > height * 0.15:  # Leave 5% margin
            font_size *= 0.9  # Reduce font size by 10%
            cr.set_font_size(font_size)
            text_extents = cr.text_extents(uptime_text)
        
        # Center the uptime text
        text_x = (width - text_extents.width) / 2
        text_y = (height + text_extents.height) / 2
        
        cr.move_to(text_x, text_y)
        cr.show_text(uptime_text)
        
        return False
    
    def update_time(self):
        """Update the time and date labels"""
        if self.time_label and self.date_label:
            now = datetime.now()
            
            # Format time (big, white, no seconds)
            time_str = now.strftime("%H:%M")
            self.time_label.set_markup(
                f'<span foreground="white" size="72000" weight="bold" font_family="monospace">{time_str}</span>'
            )
            
            # Format date (smaller, light gray)
            date_str = now.strftime("%A, %B %d, %Y")
            self.date_label.set_markup(
                f'<span foreground="#cccccc" size="18000">{date_str}</span>'
            )
        
        return True  # Continue the timer
    
    def get_weather_data(self):
        """Get weather data from wttr.in or cache"""
        try:
            # Try to fetch fresh weather data
            result = subprocess.run([
                'curl', '-s', '--connect-timeout', '5', 
                'wttr.in/dumaguete?format=j2'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                weather_data = json.loads(result.stdout)
                
                # Save to cache
                with open(self.weather_cache_file, 'w') as f:
                    json.dump(weather_data, f)
                
                return weather_data
            else:
                raise Exception("Failed to fetch weather data")
                
        except Exception:
            # Fallback to cached data
            try:
                if os.path.exists(self.weather_cache_file):
                    with open(self.weather_cache_file, 'r') as f:
                        return json.load(f)
            except Exception:
                pass
            
            return None
    
    def update_weather(self):
        """Update weather information"""
        self.weather_data = self.get_weather_data()
        if self.window:
            self.window.queue_draw()
        return True  # Continue the timer
    
    def get_uptime(self):
        """Get system uptime using uptime -p"""
        try:
            result = subprocess.run(['uptime', '-p'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "uptime unavailable"
    
    def update_uptime(self):
        """Update uptime information"""
        self.uptime_info = self.get_uptime()
        if self.window:
            self.window.queue_draw()
        return True  # Continue the timer
    
    def get_music_info(self):
        """Get current music info from kew via D-Bus"""
        try:
            session_bus = dbus.SessionBus()
            player = session_bus.get_object("org.mpris.MediaPlayer2.kew", "/org/mpris/MediaPlayer2")
            properties = dbus.Interface(player, "org.freedesktop.DBus.Properties")
            metadata = properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            playback_status = properties.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
            
            # Store the player interface for media controls
            self.media_player = dbus.Interface(player, "org.mpris.MediaPlayer2.Player")
            
            # Get title
            title = metadata.get("xesam:title", "No song playing")
            
            # Get artist (join array into a single string)
            artist = metadata.get("xesam:artist", [""])
            if isinstance(artist, list):
                artist = ", ".join(artist)  # Join multiple artists with commas
            
            # Get album art URL
            art_url = metadata.get("mpris:artUrl", None)
            
            return {
                "title": title,
                "artist": artist,
                "art_url": art_url,
                "playback_status": playback_status
            }
        except (dbus.exceptions.DBusException, Exception):
            self.media_player = None
            return {"title": "No song playing", "artist": "", "art_url": None, "playback_status": "Stopped"}
    
    def update_music_info(self):
        """Update music info periodically"""
        self.music_info = self.get_music_info()
        # Force redraw of the bottom widget
        if self.window:
            self.window.queue_draw()
        return True  # Continue the timer
    
    def load_album_art(self, art_url, target_size):
        """Load and scale album art from URL or file path"""
        if not art_url:
            return None
            
        try:
            # Handle file:// URLs
            if art_url.startswith("file://"):
                file_path = art_url[7:]  # Remove "file://" prefix
            else:
                file_path = art_url
            
            # Check if file exists
            if not os.path.exists(file_path):
                return None
                
            # Load and scale the image
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(file_path)
            scaled_pixbuf = pixbuf.scale_simple(
                target_size, target_size, GdkPixbuf.InterpType.BILINEAR
            )
            return scaled_pixbuf
        except Exception:
            return None
    
    def on_key_press(self, widget, event):
        """Handle key press events"""
        if (event.keyval == Gdk.KEY_Escape or 
            event.keyval == Gdk.KEY_space or 
            event.keyval == Gdk.KEY_Return):
            self.cleanup_and_quit()
        return True
    
    def on_button_press(self, widget, event):
        """Handle mouse click events - DISABLED for media controls"""
        # Disabled to allow media controls to work
        return True
    
    def cleanup_and_quit(self):
        """Clean up temporary files and quit"""
        # Remove temporary files
        temp_files = ['screenshot.png', 'blurred_screenshot.png']
        for filename in temp_files:
            filepath = os.path.join(self.temp_dir, filename)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except OSError:
                pass  # Ignore cleanup errors
        
        Gtk.main_quit()
    
    def run(self):
        """Main execution method"""
        print("Starting blurred screen overlay...")
        
        # Check dependencies
        if not self.check_dependencies():
            return 1
        
        # Take screenshot
        print("Taking screenshot...")
        screenshot_path = self.take_screenshot()
        if not screenshot_path:
            return 1
        
        # Blur the image
        print("Applying blur effect...")
        blurred_path = self.blur_image(screenshot_path)
        if not blurred_path:
            return 1
        
        # Create and show fullscreen window
        print("Displaying blurred overlay with clock...")
        print("Press ESC, SPACE, or ENTER to close.")
        self.create_fullscreen_window(blurred_path)
        
        # Start GTK main loop
        try:
            Gtk.main()
        except KeyboardInterrupt:
            self.cleanup_and_quit()
        
        return 0

def main():
    overlay = BlurredScreenOverlay()
    return overlay.run()

if __name__ == '__main__':
    sys.exit(main())
