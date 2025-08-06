services:
  - type: web
    name: fantasy-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: bash start.sh
