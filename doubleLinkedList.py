class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    # ── Insert ─────────────────────────────────────────────

    def append(self, data):
        """Insert at the tail."""
        node = Node(data)
        print(data)
        if self.tail is None:
            self.head = self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self.size += 1

    def prepend(self, data):
        """Insert at the head."""
        node = Node(data)
        if self.head is None:
            self.head = self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node
        self.size += 1

    def insert_after(self, target_data, data):
        """Insert a new node directly after the first node whose data matches target_data."""
        current = self.head
        while current:
            if current.data == target_data:
                if current is self.tail:
                    self.append(data)
                else:
                    node = Node(data)
                    node.prev = current
                    node.next = current.next
                    current.next.prev = node
                    current.next = node
                    self.size += 1
                return
            current = current.next
        raise ValueError(f"{target_data!r} not found in list")

    # ── Delete ─────────────────────────────────────────────

    def delete(self, data):
        """Remove the first node whose data matches."""
        current = self.head
        while current:
            if current.data == data:
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next          # removing head

                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev          # removing tail

                self.size -= 1
                return
            current = current.next
        raise ValueError(f"{data!r} not found in list")

    # ── Search ─────────────────────────────────────────────

    def find(self, data):
        """Return the first node whose data matches, or None."""
        current = self.head
        while current:
            if current.data == data:
                return current
            current = current.next
        return None

    # ── Traversal ──────────────────────────────────────────

    def to_list(self):
        """Return all values as a plain Python list (head → tail)."""
        result, current = [], self.head
        while current:
            result.append(current.data)
            current = current.next
        return result

    def to_list_reversed(self):
        """Return all values as a plain Python list (tail → head)."""
        result, current = [], self.tail
        while current:
            result.append(current.data)
            current = current.prev
        return result

    # ── Dunder helpers ─────────────────────────────────────

    def __len__(self):
        return self.size

    def __contains__(self, data):
        return self.find(data) is not None

    def __repr__(self):
        return " <-> ".join(str(v) for v in self.to_list()) or "< empty >"


# ── Quick demo ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dll = DoublyLinkedList()

    dll.append(10)
    dll.append([20])
    dll.append(30)
    dll.prepend(5)
