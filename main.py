#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lockscreen import LockScreen
from utils import create_example_files

def main():
    debug_mode = '--debug' in sys.argv
    if '--debug' in sys.argv:
        sys.argv.remove('--debug')
    
    config_file = 'lockscreen.yaml' if len(sys.argv) < 2 else sys.argv[1]
    
    if not os.path.exists(config_file):
        create_example_files()
    
    try:
        lockscreen = LockScreen(config_file, debug=debug_mode)
        lockscreen.run()
    except KeyboardInterrupt:
        print("\nLockscreen interrupted")
    except Exception as e:
        print(f"Error: {e}")
        if debug_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()