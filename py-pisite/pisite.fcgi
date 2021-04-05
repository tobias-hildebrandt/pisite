from flup.server.fcgi import WSGIServer
import pisite_app

if __name__ == "__main__":
    WSGIServer(pisite_app.app, bindAddress='/tmp/pisite.sock').run()
