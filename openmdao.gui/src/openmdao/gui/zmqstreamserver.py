import sys
import os
import traceback
import subprocess

from optparse import OptionParser

import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream

from tornado import httpserver, web, websocket

import jsonpickle

debug = True


def DEBUG(msg):
    if debug:
        print '<<<' + str(os.getpid()) + '>>> ZMQStreamServer --', msg


def make_unicode(content):
    if type(content) == str:
        # Ignore errors even if the string is not proper UTF-8 or has
        # broken marker bytes.
        # Python built-in function unicode() can do this.
        content = unicode(content, "utf-8", errors="ignore")
    else:
        # Assume the content object has proper __unicode__() method
        content = unicode(content)
    return content


class ZMQStreamHandler(websocket.WebSocketHandler):
    ''' a handler that forwards output from a ZMQStream to a WebSocket
    '''

    def initialize(self, addr):
        self.addr = addr

    def open(self):
        stream = None
        try:
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(self.addr)
            socket.setsockopt(zmq.SUBSCRIBE, '')
            stream = ZMQStream(socket)
        except Exception, err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print 'ZMQStreamHandler ERROR getting ZMQ stream:', err
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            if stream and not stream.closed():
                stream.close()
        else:
            stream.on_recv(self._write_message)

    def _write_message(self, message):
        if len(message) == 1:
            message = message[0]
            message = make_unicode(message)  # tornado websocket wants unicode
            self.write_message(message)

        elif len(message) == 2:
            topic = message[0]
            content = message[1]

            # package topic and content into a single json object
            try:
                content = jsonpickle.decode(content)
                message = jsonpickle.encode([topic, content])
            except Exception as err:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print 'ZMQStreamHandler ERROR decoding/encoding message:', topic, err
                traceback.print_exception(exc_type, exc_value, exc_traceback)
                return

            # convert to unicode (tornado websocket wants unicode)
            try:
                message = make_unicode(message)
            except Exception, err:
                exc_type, exc_value, exc_traceback = sys.exc_info
                print 'ZMQStreamHandler ERROR converting message to unicode:', topic, err
                traceback.print_exception(exc_type, exc_value, exc_traceback)
                return

            # write message to websocket
            self.write_message(message)

    def on_message(self, message):
        pass

    def on_close(self):
        DEBUG('zmqstream connection closed')


class ZMQStreamApp(web.Application):
    ''' a web application that serves a ZMQStream over a WebSocket
    '''

    def __init__(self, zmqstream_addr, websocket_url):
        handlers = [
            (websocket_url, ZMQStreamHandler, dict(addr=zmqstream_addr))
        ]
        settings = {
            'login_url': '/login',
            'debug': True,
        }
        super(ZMQStreamApp, self).__init__(handlers, **settings)


class ZMQStreamServer(object):
    ''' runs an http server that serves a ZMQStream over a WebSocket
    '''

    def __init__(self, options):
        self.options = options
        self.web_app = ZMQStreamApp(options.addr, options.url)
        self.http_server = httpserver.HTTPServer(self.web_app)

    def serve(self):
        ''' start server listening on port & start the ioloop
        '''
        self.http_server.listen(self.options.port, address="localhost")

        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            DEBUG('interrupt received, shutting down.')

    @staticmethod
    def get_options_parser():
        ''' create a parser for command line arguments
        '''
        parser = OptionParser()
        parser.add_option("-z", "--zmqstream",
                          dest="addr", default=0,
                          help="the address of the zmqstream")
        parser.add_option("-p", "--port",
                          dest="port", type="int", default=0,
                          help="the port to run websocket server on")
        parser.add_option("-u", "--url",
                          dest="url",
                          help="the url to expose for the websocket")
        return parser

    @staticmethod
    def spawn_process(zmq_url, ws_port, ws_url='/'):
        ''' run zmqstreamserver in it's own process, mapping a zmq
            stream to a websocket

            args:
            zmq_url     the url of the ZMQStream
            ws_port     the port to serve the WebSocket on
            ws_url      the url to map to the WebSocket
        '''
        file_path = os.path.abspath(__file__)
        cmd = ['python', file_path,
               '-z', str(zmq_url),
               '-p', str(ws_port),
               '-u', str(ws_url)]
        return subprocess.Popen(cmd)


def main():
    ''' process command line arguments, create server and start it up
    '''
    # make sure to install zmq ioloop before creating any tornado objects
    ioloop.install()

    # create the server and kick it off
    parser = ZMQStreamServer.get_options_parser()
    (options, args) = parser.parse_args()
    server = ZMQStreamServer(options)
    server.serve()


if __name__ == '__main__':
    # dont run main() if this is a forked windows process
    if sys.modules['__main__'].__file__ == __file__:
        main()
