# TX11Lock

A customizable lockscreen application for X11 with widget support, background blur effects, and SCSS theming.

## Features

- Takes screenshot and applies blur effect as background
- Widget-based architecture with positioning system
- SCSS styling with background support for widgets
- JSON data parsing with dot notation
- Multiple command execution per widget
- Configurable via YAML

## Requirements

### System Dependencies
```bash
# Ubuntu/Debian
sudo apt install python3-gi scrot ffmpeg

# Arch Linux  
sudo pacman -S python-gobject scrot ffmpeg

# Fedora
sudo dnf install python3-gobject scrot ffmpeg
```

### Python Dependencies
```bash
pip install PyYAML libsass
```

## Installation

1. Clone the repository
2. Install dependencies
3. Make executable: `chmod +x main.py`
4. Run: `./main.py`

## Configuration

Configuration is done via `lockscreen.yaml` and `lockscreen.scss` files, automatically created on first run.

### Basic Widget Configuration

```yaml
widgets:
  clock:
    type: "builtin.clock"
    class-name: "clock-widget"
    options:
      label: "%I:%M %p"  # strftime format
    position: "center"
    offset_x: 0
    offset_y: 0
```

### Widget Types

#### Clock Widget
Displays current time with customizable format.

```yaml
clock:
  type: "builtin.clock"
  class-name: "clock-widget"
  options:
    label: "%H:%M:%S"  # 24-hour format
  position: "center"
```

#### Custom Widget
Executes shell commands and displays output.

```yaml
weather:
  type: "builtin.custom"
  class-name: "weather-widget"
  options:
    label: "{current_condition.temp_C}°C\n{current_condition.weatherDesc.value}"
  exec_options:
    run_cmd: "curl -s 'https://wttr.in/london?format=j2'"
    run_interval: 300000  # 5 minutes in milliseconds
    return_format: "json"
  position: "northeast"
```

### Multiple Commands

Execute multiple commands in a single widget:

```yaml
system_info:
  type: "builtin.custom"
  class-name: "info-widget"
  options:
    label: "Weather: {weather.current_condition.temp_C}°C\nUptime: {system}\nDisk: {storage}"
  exec_options:
    commands:
      weather:
        run_cmd: "curl -s 'https://wttr.in/london?format=j2'"
        return_format: "json"
      system:
        run_cmd: "uptime -p"
        return_format: "text"
      storage:
        run_cmd: "df -h / | awk 'NR==2{print $5}'"
        return_format: "text"
    run_interval: 300000
  position: "southwest"
```

### Positioning

Available positions:
- `center`, `north`, `south`, `east`, `west`
- Combinations: `northeast`, `northwest`, `southeast`, `southwest`
- Fine-tune with `offset_x` and `offset_y` (pixels)

### JSON Data Access

Use dot notation to access nested JSON data. Arrays automatically use the first element unless explicitly indexed.

```yaml
# Automatic first element selection
label: "{current_condition.temp_C}°C"

# Explicit array indexing
label: "{weather.1.date}"  # Second day forecast
```

## SCSS Theming

Widgets support background styling via SCSS:

```scss
.clock-widget {
  // Background styling
  &-background {
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-top: 20px;
    margin-bottom: 20px;
    margin-left: 20px;
    margin-right: 20px;
  }
  
  // Padding inside widget
  &-padding {
    padding-top: 15px;
    padding-bottom: 15px;
    padding-left: 25px;
    padding-right: 25px;
    min-width: 200px;
    min-height: 80px;
  }
  
  // Text styling
  &-text {
    font-family: Sans;
    font-size: 48px;
    font-weight: bold;
    color: white;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
  }
}
```

### CSS Classes

Each widget generates three CSS classes:
- `{class-name}-background`: Background container styling
- `{class-name}-padding`: Padding container styling  
- `{class-name}-text`: Text content styling

## Usage

### Basic Usage
```bash
./main.py
```

### With Custom Config
```bash
./main.py myconfig.yaml
```

### Debug Mode
```bash
./main.py --debug
```

### Exit
Press Space, Enter, or Escape to close the lockscreen.

## Widget Options Reference

### Global Widget Properties
- `type`: Widget type (`builtin.clock`, `builtin.custom`)
- `class-name`: CSS class name for styling
- `position`: Widget position on screen
- `offset_x`: Horizontal pixel offset
- `offset_y`: Vertical pixel offset

### Clock Widget Options
- `label`: Time format using strftime syntax

### Custom Widget Options
- `label`: Display format with `{key.path}` substitution
- `exec_options.run_cmd`: Single command to execute
- `exec_options.commands`: Multiple commands (dict format)
- `exec_options.run_interval`: Update interval in milliseconds
- `exec_options.return_format`: `json` or `text`

## Examples

### Weather Display
```yaml
weather:
  type: "builtin.custom"
  class-name: "weather-widget"
  options:
    label: "{current_condition.temp_C}°C - {current_condition.weatherDesc.value}"
  exec_options:
    run_cmd: "curl -s 'https://wttr.in/london?format=j2'"
    return_format: "json"
    run_interval: 300000
  position: "northeast"
  offset_x: -20
  offset_y: 20
```

### System Status
```yaml
system:
  type: "builtin.custom"
  class-name: "system-widget" 
  options:
    label: "CPU: {cpu}%\nRAM: {memory}%\nUptime: {uptime}"
  exec_options:
    commands:
      cpu:
        run_cmd: "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
        return_format: "text"
      memory:
        run_cmd: "free | awk 'NR==2{printf \"%.0f\", $3*100/$2}'"
        return_format: "text"
      uptime:
        run_cmd: "uptime -p | sed 's/up //'"
        return_format: "text"
    run_interval: 5000
  position: "southwest"
```

## Troubleshooting

### Widget Not Appearing
1. Check YAML syntax
2. Verify command executes correctly: `bash -c "your_command_here"`
3. Run with `--debug` flag to see detailed output
4. Check widget positioning and offsets

### JSON Parsing Errors
1. Test JSON output: `your_command | jq .`
2. Verify return_format is set to "json"
3. Check for trailing characters in command output

### Styling Issues
1. Install libsass: `pip install libsass`
2. Check SCSS syntax
3. Verify CSS class names match widget class-name
4. Use browser developer tools concepts for debugging

### Performance Issues
1. Increase run_interval values
2. Reduce command complexity
3. Cache command results where possible


