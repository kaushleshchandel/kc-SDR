import os
from taskbar_launcher import TaskbarLauncher

if __name__ == "__main__":
    # Ensure the script uses the main display
    os.environ['DISPLAY'] = ':0'
    app = TaskbarLauncher()
    app.run()