from enum import Enum

class CallPosition(Enum):
    FIRST = "first"    # first_node
    LAST = "last"      # last_node
    BETWEEN = "between"
    BOTH = "both"      # first and last node