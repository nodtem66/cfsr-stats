# Simple progress: single . = 100 records
def print_progress(count: int, minor: int = 10, major: int = 50):
    print(".", end="", flush=True)
    if count % minor == minor - 1:
        print(" ", end="")
    if count % major == major - 1:
        print(flush=True)