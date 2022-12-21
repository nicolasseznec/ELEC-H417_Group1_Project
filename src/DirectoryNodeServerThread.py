from ConnectionsThread import *
from NodeServerThread import NodeServerThread


class DirectoryNodeServerThread(NodeServerThread):
    def run(self):
        while not self.flag.is_set():
            try:
                client_sock, client_address = self.sock.accept()
                self.handle_connection(client_sock, client_address)

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            while not self.diconnections.empty():
                address = self.diconnections.get()
                connection = self.connection_threads.pop(address, None)
                connection.stop()

                print(f"disonnected : {address}")
                self.node.unregister_node(address)

        for connection in self.connection_threads.values():
            connection.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def create_connection(self, sock, client_address):
        return ConnectionThread(self.node.message_queue, self.diconnections, sock, client_address, timeout=40)

    def create_pinger(self, message_queue, address):
        return None
