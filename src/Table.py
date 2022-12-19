
class Table:
    """
    # key table
    {(id, addr): key}

    # Transfer table
    {(id, addr): (id, addr)}
    """
    def __init__(self):
        self.key_table = {}
        self.transfer_table = {}

    def new_key(self, id, addr, key):
        if not (id, addr) in self.key_table:
            self.key_table[(id, addr)] = key

    def get_key(self, id, addr):
        if (id, addr) in self.key_table:
            # To decrypt
            return self.key_table[(id, addr)]

        if (id, addr) in self.transfer_table:
            # To encrypt
            (left_id, left_addr) = self.transfer_table[(id, addr)]
            return self.key_table[(left_id, left_addr)]

        return None

    def new_transfer(self, left_id, left_addr, right_id, right_addr):
        # just decrypted
        if (right_id, right_addr) not in self.transfer_table:
            self.transfer_table[(right_id, right_addr)] = (left_id, left_addr)
            return True
        else:
            if self.transfer_table[(right_id, right_addr)] == (left_id, left_addr):
                return True
            else:
                # Duplicate
                return False

    def get_transfer(self, id, addr):
        if (id, addr) in self.transfer_table:
            return self.transfer_table[(id, addr)]
        else:
            return None

    def drop_path(self, right_id, right_addr):
        if (right_id, right_addr) in self.transfer_table:
            (left_id, left_addr) = self.transfer_table[(right_id, right_addr)]
            self.transfer_table.pop((right_id, right_addr))
            self.drop_key(left_id, left_addr)

    def drop_key(self, id, addr):
        if (id, addr) in self.key_table:
            self.key_table.pop((id, addr))
