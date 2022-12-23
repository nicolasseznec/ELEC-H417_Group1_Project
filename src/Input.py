import threading
import argparse

from Request import construct_request
import constants


class InputHandler(threading.Thread):
    """
    Thread that handles the client input
    """
    def __init__(self, node):
        super().__init__()
        self.flag = threading.Event()
        self.node = node

        self.parser = argparse.ArgumentParser(prog="")
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-r", "--request", nargs=2, metavar=("REQUEST", "URL"), help="make a request")
        group.add_argument("-l", "--login", nargs=2, metavar=("USERNAME", "PASSWORD"), help="login")
        group.add_argument("-stop", action='store_true', help="stop the connection")
        group.add_argument("-debug", action='store_true', help="Enables debug prints")

    def run(self):
        while not self.flag.is_set():
            try:
                string = input("Enter a command : ")
                print('-----------------------------------')
                args = string.split()
                command = self.parser.parse_args(args)

                if command.stop:
                    self.node.stop_connection()

                if command.debug:
                    constants.DEBUG = True

                if command.login:
                    print("Authenticating...")
                    username = command.login[0]
                    password = command.login[1]
                    self.node.authenticate(username, password,
                                           (constants.AUTHENTICATION_SERV_HOST, constants.AUTHENTICATION_SERV_PORT))

                if command.request:
                    print("Processing request...")
                    method = command.request[0]
                    method = method.lower()
                    url = command.request[1]
                    request = construct_request(method, url)
                    self.node.message_tor_send(request, "request")

            except Exception as e:
                raise e

            except SystemExit:
                # Do not exit on wrong command
                pass

    def stop(self):
        self.flag.set()
