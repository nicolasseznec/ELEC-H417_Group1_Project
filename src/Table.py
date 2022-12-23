class Table:
    """
    Routing table of a node

    # key table
    {(id, addr): key}

    # Transfer table
    {(id, addr): (id, addr)}
    """
    def __init__(self):
        self.key_table = {}
        self.transfer_table = {}

    def new_key(self, msg_id, addr, key):
        if not (msg_id, addr) in self.key_table:
            self.key_table[(msg_id, addr)] = key

    def get_key(self, msg_id, addr):
        if (msg_id, addr) in self.key_table:
            # To decrypt
            return self.key_table[(msg_id, addr)]

        if (msg_id, addr) in self.transfer_table:
            # To encrypt
            (left_id, left_addr) = self.transfer_table[(msg_id, addr)]
            return self.key_table[(left_id, left_addr)]

        return None

    def new_transfer(self, left_id, left_addr, right_id, right_addr):
        """
        Adds a transfer in the transfer table
        :param left_id: The id of the message coming from the "entry node side"
        :param left_addr: The address of message coming from the "entry node side"
        :param right_id: The id of the message coming from the "exit node side"
        :param right_addr: The address of message coming from the "exit node side"
        """
        self.transfer_table[(right_id, right_addr)] = (left_id, left_addr)

    def get_transfer(self, msg_id, addr):
        if (msg_id, addr) in self.transfer_table:
            return self.transfer_table[(msg_id, addr)][0], self.transfer_table[(msg_id, addr)][1]
        else:
            return None

    def drop_path(self, right_id, right_addr):
        """
        Deletes the information bound to this path in all the tables
        """
        if (right_id, right_addr) in self.transfer_table:
            (left_id, left_addr) = self.transfer_table[(right_id, right_addr)]
            self.transfer_table.pop((right_id, right_addr))
            self.drop_key(left_id, left_addr)

    def drop_key(self, msg_id, addr):
        if (msg_id, addr) in self.key_table:
            self.key_table.pop((msg_id, addr))
