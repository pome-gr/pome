#!python3.9
import sys

from pome import app

PORT = 5000

if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        PORT = 5000

app.run(debug=True, port=PORT)
