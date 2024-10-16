import json
import logging
import os
import socketserver
from http import server
from config import Config
from dish import Dish

logger = logging.getLogger(__name__)


class Server(socketserver.ThreadingMixIn, server.HTTPServer):
    # A simple HTTP server allowing IO over a webpage

    instance: any
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, requestHandler):
        super().__init__(address, requestHandler)

    def run(self):
        logger.info('Server running at' +
                    str(Server.instance.server_address))
        try:
            # Set up and start the server
            self.serve_forever()
        finally:
            # Stop serving when the script is interrupted
            logger.info("Server stopped.")

    def start():
        Server.port = Config.getWebPort()
        # This creates an instance of the server class and runs it
        logger.debug('starting server...')
        logger.debug('sever port %i', Server.port)
        address = ('', Server.port)
        Server.instance = Server(address, RequestHandler)
        Server.instance.run()

    def stop():
        # This shuts the instance down and stops all camera streams
        logger.debug('stopping server')
        try:
            Server.instance.shutdown()
            Server.instance.server_close()
        except AttributeError:
            return
        # Server.instance.shutdown()
        # Server.instance.server_close()


class RequestHandler(server.SimpleHTTPRequestHandler):
    # This handles the requests sent to the http server (from the fetch function in index.js for example)
    # Requests always contain a path/url that describes what the request wants from the server

    def do_GET(self):
        # read the request url and call the appropriate function
        if self.path == '/':
            self.redirectHome(permanently=True)

        elif self.path == '/favicon.ico':
            self.sendFile('src/client/favicon.ico')

        elif self.path == '/index.html':
            self.sendFile('src/client/index.html')

        elif self.path == '/index.js':
            self.sendFile('src/client/index.js')

        else:
            # An unknown request was sent
            server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/':
            self.redirectHome()
        elif self.path == "/api/set-target":

            # Get the length of the data
            content_length = int(self.headers['Content-Length'])

            # Read the data sent in the POST request
            post_data = self.rfile.read(content_length)

            # Convert the data from JSON to a Python dictionary
            data = json.loads(post_data.decode('utf-8'))

            # Extract the two values from the data
            azimuth = data.get('azimuth')
            elevation = data.get('elevation')
            logger.info(f"Received new position: {azimuth}, {elevation}")
            Dish.set_target(float(azimuth), float(elevation))
            self.redirectHome()

    def redirectHome(self, permanently=False):
        if permanently:
            self.send_response(301)
        else:
            self.send_response(302)
        self.send_header('Location', '/index.html')
        self.end_headers()

    def sendPageNotFound(self):
        self.send_error(404)
        self.end_headers()

    def sendFile(self, filePath):
        # This opens a file on the raspberry and sends that to the webpage
        logger.debug("sending file: " + filePath)
        if not os.path.isfile(filePath):
            # If the file does not exist, send a warning and redirect to the home page
            logger.warn('File does not exist: ' + filePath)
            self.redirectHome()
            return

        # The built-in class "SimpleHTTPRequestHandler", which this class extends, already has this functionality
        # This wrapper allows us to have the request path and the file path not be the same, and handle non-existent files correctly as above
        self.path = filePath
        server.SimpleHTTPRequestHandler.do_GET(self)
