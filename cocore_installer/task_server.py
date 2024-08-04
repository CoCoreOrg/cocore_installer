import json
import tornado.ioloop
import tornado.web
import tornado.websocket
import time
import uuid

connected_vms = {}

class VMHandler (tornado.websocket.WebSocketHandler):
    """
    A class to handle web socket connections from VMs.
    """

    id = None

    def open(self):
        print('Opened connection')
        self.id = str(uuid.uuid4())
        connected_vms[self.id] = self

    def on_close(self):
        print('Closed connection')
        del connected_vms[self.id]

class WebHandler (tornado.web.RequestHandler):
    def get(self):
        self.write("""<!doctype html>
<html>
    <head>
        <title>CoCore Test Server</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    </head>

    <body>
        <form method="post">
            <div class="container mt-3">
                <div class="form-group mb-3">
                    <label>Command</label>
                    <input class="form-control" name="command" style="font-family: monospace;" autofocus />
                </div>
                <button class="btn btn-primary">Run Command</button>
            </div>
        </form>
    </body>
</html>
        """)

    def post(self):
        command = self.get_argument('command')
        print('POST: ' + command)
        for vm in connected_vms.values():
            vm.write_message(json.dumps({
                "command": command,
            }))
        return self.get()

application = tornado.web.Application([
    (r'/vm', VMHandler),
    (r'/', WebHandler),
])

def start_server():
    print('Starting server on http://*:3001')
    application.listen(3001)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    start_server()
