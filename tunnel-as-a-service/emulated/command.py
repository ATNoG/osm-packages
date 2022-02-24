class Command:
    def __init__(self, command, initial_status, ok_status, error_status):
        self.command = command
        self.initial_status = initial_status
        self.ok_status = ok_status
        self.error_status = error_status