"""
FIXTURE: Unreachable Code

This Python file contains code after return/raise statements
that can never be executed.

EXPECTED FINDING: unreachable_code (WARNING severity)
EVIDENCE REQUIRED: Control flow analysis
"""


def process_data(data):
    """Function with unreachable code after return."""
    if not data:
        return None
        print("This will never print")  # UNREACHABLE
        x = 1 + 2  # UNREACHABLE

    return data


def validate_input(value):
    """Function with unreachable code after raise."""
    if value < 0:
        raise ValueError("Value must be positive")
        log_error("Negative value")  # UNREACHABLE
        return False  # UNREACHABLE

    return True


def early_exit():
    """Function that always exits early."""
    return "early"
    # Everything below is unreachable
    print("Setting up...")
    result = complex_calculation()
    return result


# TODO: Fix unreachable code above
# FIXME: This function has issues


def complex_calculation():
    """This function is never called due to early_exit."""
    return 42
