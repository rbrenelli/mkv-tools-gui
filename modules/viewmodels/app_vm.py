
class AppViewModel:
    def __init__(self):
        # We might hold global state here or refs to other VMs
        self.current_view = "Extract"
        self.is_busy = False

    def set_view(self, view_name: str):
        self.current_view = view_name
