okay very nice lets have a new module:

custom module

```yaml
widgets:
  weather:
    type: "builtin.custom"
    class-name: "weather-widget"
    options:
      label: "{thing.in.json} \n {thing.yeah}" # it takes the data from the json using this and adds a newline
    exec_options:
      run_cmd: "example command that outputs json" # like a curl of https://wttr.in/london?format=j2
      run_interval: 120000  # every 5 minutes
      return_format: "json" # turns the json formatter on so it recognizes it
```

i want it to be able to query using that format using dots to separate the data sections cause its easier
i also want it to support newlines

also i want to add a new thing for the yaml called `class-name` for the css since i think it would me much easier to manage if you have multiple weather widgets and want to combine stuff in a single class class-name
