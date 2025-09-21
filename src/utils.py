import os

def create_example_files():
    """Create example configuration and CSS files"""
    
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
    
    # Example CSS
    css_content = """/* Lockscreen CSS Styling */

.clock-widget {
    font-family: Sans;
    font-size: 48px;
    font-weight: bold;
    color: white;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
}

.weather-widget {
    font-family: Sans;
    font-size: 18px;
    color: white;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
}

/* You can add more widget styles here */
"""
    
    # Write example files if they don't exist
    if not os.path.exists('lockscreen.yaml'):
        with open('lockscreen.yaml', 'w') as f:
            f.write(config_yaml)
        print("Created example lockscreen.yaml")
    
    if not os.path.exists('lockscreen.css'):
        with open('lockscreen.css', 'w') as f:
            f.write(css_content)
        print("Created example lockscreen.css")
