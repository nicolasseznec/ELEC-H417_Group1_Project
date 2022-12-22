import threading
import argparse

from src.Request import construct_request
from src.constants import LOCALHOST


class InputHandler(threading.Thread):
    """
    Thread that handles the client input
    """
    def __init__(self, node):
        super(InputHandler, self).__init__()
        self.flag = threading.Event()
        self.node = node

        self.parser = argparse.ArgumentParser(prog="")
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-r", "--request", nargs=2, metavar=("REQUEST", "URL"), help="make a request")
        group.add_argument("-l", "--login", nargs=2, metavar=("USERNAME", "PASSWORD"), help="login")
        group.add_argument("-stop", action='store_true', help="stop the connection")

    def run(self):
        while not self.flag.is_set():
            try:
                string = input("Enter a command : ")
                print('-----------------------------------')
                args = string.split()
                command = self.parser.parse_args(args)

                if command.stop:
                    self.node.stop_connection()

                if command.login:
                    username = command.login[0]
                    password = command.login[1]
                    pass  # login

                if command.request:
                    method = command.request[0]
                    method = method.lower()
                    url = command.request[1]
                    request = construct_request(method, url)
                    # print(request)
                    self.node.message_tor_send(request, "request")

                # arg = string.split()
            #     if arg[0] == "--help":
            #         self.print_help()
            #     if arg[0] == "--request" or arg[0] == "-r":
            #         if arg[1] in REQUEST_METHODS:
            #             method = arg[1]
            #             url = arg[2]
            #             request = construct_request(method, url)
            #             self.node.message_tor_send(request, "request")
            #     if arg[0] == "-stop":
            #         self.node.stop_connection()
            #     else:
            #         self.print_help()
            #
            # except IndexError:
            #     print("Not enough arguments \n"
            #           "Type --help for help")
            #

            except Exception as e:
                raise e

            except SystemExit:
                # Does not exit on wrong command
                pass

    # def print_help(self):
    #     help_text = "Type --help for help \n" \
    #                 "To send a request, type -r request_method url"
    #     print(help_text)

    def stop(self):
        self.flag.set()


# if __name__ == '__main__':
#     InputHandler(None).start()
