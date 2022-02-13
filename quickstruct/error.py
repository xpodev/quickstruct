class QuickStructError(Exception):
    """Base class for all QuickStruct errors."""
    pass


class FieldError(QuickStructError):
    """Base class for all field errors."""
    pass


class OverrideError(FieldError):
    """Raised when a field is override is not allowed."""
    pass


class UnoverridbaleFieldError(FieldError):
    """Raised when a field is overriding a locked field."""
    pass


class UnsafeOverrideError(FieldError):
    """Raised when a field is overriding a field with a different type when the struct is marked as SafeOverride."""
    pass


class InheritanceError(QuickStructError):
    """Raised when an invalid inheritance is detected."""
    pass


class SizeError(QuickStructError):
    """Raised when an invalid size is detected."""
    pass
