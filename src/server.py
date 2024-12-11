import json
import os
import logging
import socketserver
from http import server
from config import Config
from dish import Dish

# To be moved to user manual:
# When the raspberry hosts the website, it is not publicly available, only on the local network. This would mean only on eduroam
# However, eduroam is quite protected and does not allow this kind of stuff (might be possible with certain config, but not now)
# The way around this is to create a local mini network by plugging an ethernet cable from the raspberry to a laptop.
# It is then available on the laptop only

logger = logging.getLogger(__name__)

# This is what hosts the web interface
# The website is divided in a server and a client, both of them run a part of the program
# This file defines the server and is run on the raspberry pi.
# The client part is defined by all the files in the client folder, and is run on the client device (your laptop or phone)
# http is the protocol they use to communicate, all of that is standardized and done by the "server" part included in python
# This class serves to deliver the html and js files from the client folder to the client device when requested
# and to call functions in dish.py when the client requests them.
# This class extends the default pyhton httpserver, meaning there is lots of functionality hidden behind that


class Server(socketserver.ThreadingMixIn, server.HTTPServer):

    # Standard pyhton server stuff
    instance: any
    allow_reuse_address = True
    daemon_threads = True

    # initialize the server, done by pyhton
    def __init__(self, address, requestHandler):
        super().__init__(address, requestHandler)

    # Start the http server and wait indefinitely for user requests
    def run(self):
        logger.info('Server running at' +
                    str(Server.instance.server_address))
        try:
            # Set up and start the server
            self.serve_forever()
        finally:
            # Stop serving when the program stops or crashes
            logger.info("Server stopped.")

    # Start the server
    def start():
        Server.port = Config.getWebPort()
        # This creates an instance of the server class and runs it
        # It is a bit weird how this class creates an instance of itself. Can be done neater
        logger.debug('starting server...')
        logger.debug('sever port %i', Server.port)
        address = ('0.0.0.0', Server.port)
        Server.instance = Server(address, RequestHandler)
        Server.instance.run()

    # Stop the server
    def stop():
        # This shuts the instance down and stops all camera streams
        logger.debug('stopping server')
        try:
            Server.instance.shutdown()
            Server.instance.server_close()
        except AttributeError:
            return

# This class is where all the requests from the client are received.
# Requests are separated into get and post requests.
# Get requests mean the client expects some result back (it is getting something from the server)
# Post requests mean the client has some extra data (it is posting something to the server)
# Each request contains a path or url that specifies what the client is requesting


class RequestHandler(server.SimpleHTTPRequestHandler):
    # This handles the requests sent to the http server (from the fetch function in index.js for example)
    # Requests always contain a path/url that describes what the request wants from the server

    def do_GET(self):
        # read the request url and call the appropriate function
        if self.path == '/':  # homepage
            self.redirectHome(permanently=True)

        elif self.path == '/favicon.ico':  # icon at the top of the tab
            self.sendFile('src/client/favicon.ico')

        elif self.path == '/index.html':  # the html page that contains the layout of the website
            self.sendFile('src/client/index.html')

        elif self.path == '/index.js':  # the javascript file that runs the logic of the website
            self.sendFile('src/client/index.js')

        elif self.path == "/api/get-current-position":  # request the current positions of the dish
            # Get the sensor data
            yaw, roll, pitch = Dish.sensor.euler
            data = {
                "azimuth": yaw,
                "elevation": roll
            }
            # Convert the data to a JSON string
            response_data = json.dumps(data)

            # Set the response headers and status
            self.send_response(server.HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # Write the JSON response back to the client
            self.wfile.write(response_data.encode("utf-8"))

        else:
            # An unknown request was sent
            server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/':
            self.redirectHome()
        elif self.path == "/api/set-target":  # Set a new target for the pid controller

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

            # Pass the order to the dish class
            Dish.set_target(float(azimuth), float(elevation))
            self.redirectHome()  # return something to let the client know its request is processed

        # move the dish to zero (not implemented)
        elif self.path == "/api/zero":
            Dish.zero()  # Pass the order to the dish class
            self.redirectHome()  # return something to let the client know its request is processed

        elif self.path == "/api/calibrate":  # perform the calibration sequence
            Dish.calibrate()  # Pass the order to the dish class
            self.redirectHome()  # return something to let the client know its request is processed

        elif self.path == "/api/toggle-pid":  # turn the pid controller on or off
            # using toggle reduces the need to pass a variable for on or off
            Dish.toggle_pid()  # Pass the order to the dish class
            self.redirectHome()  # return something to let the client know its request is processed

        elif self.path == "/api/set-pid":  # set the pid tuning variables

            # Get the length of the data
            content_length = int(self.headers['Content-Length'])

            # Read the data sent in the POST request
            post_data = self.rfile.read(content_length)

            # Convert the data from JSON to a Python dictionary
            data = json.loads(post_data.decode('utf-8'))

            # Extract the three values from the data
            p = float(data.get('p'))
            i = float(data.get('i'))
            d = float(data.get('d'))
            # if type is "elevation" elevation is true, otherwise elevation is false (so this defaults to azimuth)
            elevation = data.get('type') == "elevation"

            # pass the new values to the dish class
            Dish.tune_pid(p, i, d, elevation)

            logger.info(f"Received new pid: {p}, {i}, {d}")
            self.redirectHome()  # return something to let the client know its request is processed

    # return the index.html page
    def redirectHome(self, permanently=False):
        if permanently:
            # this tells the client to not request this anymore but load the homepage from its cache
            self.send_response(301)
        else:
            # this tells the client this was a one off page and request a new one next time
            self.send_response(302)
        self.send_header('Location', '/index.html')
        self.end_headers()

    # the client has requested a page we don't have, so we return 404
    def sendPageNotFound(self):
        self.send_error(404)
        self.end_headers()

    # Send a file to the client
    def sendFile(self, filePath):
        # This opens a file on the raspberry and sends that to the webpage
        logger.debug("sending file: " + filePath)
        if not os.path.isfile(filePath):
            # If the file does not exist, send a warning and redirect to the home page
            logger.warning('File does not exist: ' + filePath)
            self.redirectHome()
            return

        # The built-in class "SimpleHTTPRequestHandler", which this class extends, already has this functionality
        # This wrapper allows us to have the request path and the file path not be the same, and handle non-existent files correctly as above
        self.path = filePath
        # let the built-in class handle the file requests
        server.SimpleHTTPRequestHandler.do_GET(self)
