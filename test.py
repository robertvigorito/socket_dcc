class DoSomething:
    def __init__(self, value):
        self.value = value

    def perform_action(self):
        print(f"Performing action with value: {self.value}")


c = DoSomething(42)
c.perform_action()


raise ValueError("This is a test exception for demonstration purposes.")
