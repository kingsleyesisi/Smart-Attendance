import os 

COMMANDS = [
    'python manage.py makemigrations',
    'python manage.py migrate',
    'python manage.py runserver'
]
def run_commands():
    for command in COMMANDS:
        os.system(command)
        
if __name__ == "__main__":
    run_commands()
# This script automates the process of running Django management commands.