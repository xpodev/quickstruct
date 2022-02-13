from enum import IntFlag
import typing

from .common import Type


class FieldFlags(IntFlag):
    NONE = 0
    """No flags set."""
    Protected = 1 << 0
    """If set, the field can't be overridden by a derived struct."""


class StructField:
    _type: typing.Type[Type]
    _name: str

    def __init__(self, typ: typing.Type[Type]) -> None:
        self._type = typ

    def __set_name__(self, _, name):
        self._name = f"__field_{name}__"

    def __get__(self, instance, _):
        if instance is None:
            return self
        return getattr(instance, self._name)

    def __set__(self, instance, value):
        if not isinstance(value, self._type):
            raise TypeError(f"Expected {self._type}, got {type(value)}")
        setattr(instance, self._name, value)


class StructPaddingField:
    _name: str

    def __set_name__(self, _, name):
        self._name = f"__field_{name}__"

    def __get__(self, instance, _):
        if instance is None:
            return self
        return None


class FieldInfo:
    _name: str
    _type: Type
    _offset: int
    _flags: FieldFlags

    def __init__(self, name: str, typ: Type, flags: FieldFlags = FieldFlags.NONE) -> None:
        if name is None:
            raise TypeError("Field name must not be None")
        if typ is None:
            raise TypeError("Field type must not be None")
        self._name = name
        self._type = typ
        self._offset = 0
        self._flags = flags

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def type(self) -> Type:
        return self._type

    @type.setter
    def type(self, typ: Type) -> None:
        self._type = typ

    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, value: int) -> None:
        self._offset = value

    @property
    def flags(self) -> FieldFlags:
        return self._flags

    @flags.setter
    def flags(self, value: FieldFlags) -> None:
        self._flags = value

    @property
    def is_protected(self) -> bool:
        return self._flags & FieldFlags.Protected

    def __repr__(self) -> str:
        return f"{self._name}: {self._type}"
