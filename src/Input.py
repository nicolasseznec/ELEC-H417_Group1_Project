import threading

from src.Request import construct_request
from src.constants import REQUEST_METHODS, LOCALHOST


class InputHandler(threading.Thread):
    """
    Thread that handles the client input
    """
    def __init__(self, node):
        super(InputHandler, self).__init__()
        self.flag = threading.Event()
        self.node = node

    def run(self):
        while not self.flag.is_set():
            try:
                string = input("Type please : ")
                arg = string.split()
                if arg[0] == "--help":
                    self.print_help()
                if arg[0] == "--request" or arg[0] == "-r":
                    if arg[1] in REQUEST_METHODS:
                        method = arg[1]
                        url = arg[2]
                        request = construct_request(method, url)
                        self.node.message_tor_send(request, "request")
                if arg[0] == "-stop":
                    self.node.stop_connection()
                else:
                    self.print_help()

            except IndexError:
                print("Not enough arguments \n"
                      "Type --help for help")

            except Exception as e:
                raise e

    def print_help(self):
        help_text = "Type --help for help \n" \
                    "To send a request, type -r request_method url"
        print(help_text)

    def stop(self):
        self.flag.set()



