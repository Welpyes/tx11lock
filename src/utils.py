import os

def create_example_files():
    """Create example configuration and SCSS files"""
    
    # Example YAML configuration
    config_yaml = """widgets:
  clock:
    type: "builtin.clock"
    class-name: "clock-widget"  # CSS class name
    options:
      label: "%I:%M %p"  # strftime format string
    position: "center"  # position: north, south, east, west, and combinations
    offset_y: 0  # offset from the position by pixels. can be negative
    offset_x: 0  # same as the offset y

  # Example weather widget (uncomment and add your location)
  # weather:
  #   type: "builtin.custom"
  #   class-name: "weather-widget"
  #   options:
  #     # Arrays automatically use first element - no need for .0!
  #     label: "{current_condition.temp_C}°C\\n{current_condition.weatherDesc.value}"
  #   exec_options:
  #     run_cmd: "curl -s 'https://wttr.in/dumaguete?format=j2'"
  #     run_interval: 300000  # 5 minutes in milliseconds  
  #     return_format: "json"
  #   position: "northeast"
  #   offset_x: -20
  #   offset_y: 20
"""
    
    # Example SCSS with background support
    scss_content = """/* Lockscreen SCSS Styling with Background Support */

// Variables for easy theming
$primary-color: white;
$shadow-color: rgba(0, 0, 0, 0.7);
$background-blur: rgba(0, 0, 0, 0.3);

// Clock widget styling
.clock-widget {
  // Background container (EventBox)
  &-background {
    background-color: transparent; // Default: no background
    border-radius: 0px;
    border: 0px solid transparent;
    
    // GTK margins (spacing around the widget)
    margin-top: 0px;
    margin-bottom: 0px; 
    margin-left: 0px;
    margin-right: 0px;
  }
  
  // Padding container (Box inside EventBox)
  &-padding {
    // GTK padding (spacing inside the widget)
    padding-top: 0px;
    padding-bottom: 0px;
    padding-left: 0px; 
    padding-right: 0px;
    
    // Set minimum size for the container
    min-width: 0px;
    min-height: 0px;
  }
  
  // Text styling
  &-text {
    font-family: Sans;
    font-size: 48px;
    font-weight: bold;
    color: $primary-color;
    text-shadow: 2px 2px 4px $shadow-color;
  }
}

// Weather widget example with background and padding
.weather-widget {
  // Background with styling
  &-background {
    background-color: $background-blur;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    
    // Margins around the widget
    margin-top: 8px;
    margin-bottom: 8px;
    margin-left: 8px;
    margin-right: 8px;
  }
  
  // Padding inside the widget  
  &-padding {
    padding-top: 12px;
    padding-bottom: 12px;
    padding-left: 16px;
    padding-right: 16px;
    
    // Ensure minimum size
    min-width: 100px;
    min-height: 50px;
  }
  
  // Text styling  
  &-text {
    font-family: Sans;
    font-size: 18px;
    color: $primary-color;
    text-shadow: 1px 1px 3px $shadow-color;
  }
}

/* Example: Clock with a nice background */
.fancy-clock-widget {
  &-background {
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 15px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    margin-top: 20px;
    margin-bottom: 20px;
    margin-left: 20px;
    margin-right: 20px;
  }
  
  &-padding {
    padding-top: 20px;
    padding-bottom: 20px;
    padding-left: 30px;
    padding-right: 30px;
    min-width: 200px;
    min-height: 80px;
  }
  
  &-text {
    font-family: Sans;
    font-size: 48px;
    font-weight: bold;
    color: white;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
  }
}

/* You can use SCSS features like variables and nesting! */
"""
    
    # Write example files
    if not os.path.exists('lockscreen.yaml'):
        with open('lockscreen.yaml', 'w') as f:
            f.write(config_yaml)
        print("Created example lockscreen.yaml")
    
    if not os.path.exists('lockscreen.scss'):
        with open('lockscreen.scss', 'w') as f:
            f.write(scss_content)
        print("Created example lockscreen.scss")
        print("Note: Install libsass for SCSS compilation: pip install libsass")
