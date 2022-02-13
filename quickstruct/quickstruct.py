from .common import *
from .common import TypeMeta
from .error import InheritanceError, UnoverridbaleFieldError, OverrideError, SizeError, UnsafeOverrideError
from .field import FieldFlags, StructField, StructPaddingField
from .struct_builder import FieldInfo, StructBuilder, StructFlags

from io import BytesIO
import typing


class DataStructMeta(TypeMeta):
    __sflags__: StructFlags
    __size__: int
    __fields__: typing.Dict[str, FieldInfo]

    @property
    def fields(self) -> typing.List[FieldInfo]:
        return list(self.__fields__.values())

    @property
    def is_final(self) -> bool:
        """
        Returns True if this struct is final.
        """
        return bool(self.__sflags__ & StructFlags.Final)

    @property
    def is_protected(self) -> bool:
        """
        Returns True if the struct is protected.
        """
        return bool(self.__sflags__ & StructFlags.Protected)

    @property
    def alignment(self) -> int:
        """
        Returns the alignment of the struct (which is the size of the struct).
        """
        return self.size

    @property
    def size(self) -> int:
        """
        Returns the size of the struct. If the struct has dynamic size, this will return -1.
        """
        return self.__size__

    @property
    def is_dynamic_size(self):
        return self.size == -1

    @property
    def is_fixed_size(self):
        return not self.is_dynamic_size

    @classmethod
    def __prepare__(cls, _, bases, flags: StructFlags = StructFlags.Default, **__):
        namespace = {}

        fields: typing.List[FieldInfo] = []

        for base in bases:
            if not isinstance(base, DataStructMeta):
                continue
            if base.is_final:
                raise InheritanceError(f"Cannot inherit from a final struct '{base.__name__}'.")
            fields.extend(base.__fields__.values())

        namespace['__fields__'] = fields
        namespace['__sflags__'] = flags

        return namespace

    def __new__(cls, name, bases, namespace, flags: StructFlags = StructFlags.Default, **_):
        base_fields: typing.List[FieldInfo] = namespace['__fields__']
        flags: StructFlags = namespace['__sflags__']

        try:
            annotations = namespace['__annotations__']
        except KeyError:
            annotations = {}

        fields: typing.Dict[str, FieldInfo] = {}

        defaults = {n: v for n, v in namespace.items() if n in annotations}
        namespace = {n: v for n, v in namespace.items() if n not in annotations}

        field_flags: FieldFlags = FieldFlags.NONE
        if flags & StructFlags.Protected:
            field_flags |= FieldFlags.Protected

        for field in base_fields + [FieldInfo(name, typ, field_flags) for name, typ in annotations.items()]:
            if field.name in fields:
                if fields[field.name].is_protected:
                    raise UnoverridbaleFieldError(f"Field '{field.name}' is protected and cannot be overridden.")
                if flags & StructFlags.TypeSafeOverride and field.type != fields[field.name].type:
                    raise UnsafeOverrideError(f"Field '{field.name}' is overriding a field from a base type with a different type.")
                if not flags & StructFlags.AllowOverride:
                    raise OverrideError(f"Field '{field.name}' is overriding a field from a base type.")
            fields[field.name] = field
        
        builder = StructBuilder()
        for field in fields.values():
            builder.add_field(field)
        if flags & StructFlags.ReorderFields:
            builder.reorder_fields()
        if not flags & StructFlags.NoAlignment:
            builder.align_fields(None if flags & StructFlags.AlignAuto else (1 << flags & StructFlags.AlignmentMask))
        fields = {field.name: field for field in builder.build()}

        if flags & StructFlags.ForceFixedSize and builder.is_dynamic_size:
            raise SizeError(f"Cannot force fixed size on a dynamic struct '{name}'.")

        namespace['__slots__'] = tuple(f"__field_{field}__" for field in fields.keys())
        namespace['__defaults__'] = defaults
        namespace['__fields__'] = fields
        namespace['__size__'] = builder.size

        namespace.update({
            field.name: StructField(field.type) if not issubclass(field.type, Padding) else StructPaddingField()
            for field in fields.values()
            })

        return super().__new__(cls, name, bases, namespace, **_)

    def __iter__(self):
        return iter(self.__fields__.values())

    def __repr__(self) -> str:
        if not self.__fields__:
            return "{}"
        return str({field.name: field.type for field in self.__fields__.values()})


class DataStruct(Type, metaclass=DataStructMeta):
    """Base type for all data structures."""

    def __init__(self, **kwargs) -> None:
        super().__init__()
        try:
            for name in type(self).__fields__:
                if name in kwargs:
                    value = kwargs[name]
                elif name in type(self).__defaults__:
                    value = type(self).__defaults__[name]
                else:
                    continue
                setattr(self, name, value)
        except KeyError:
            raise TypeError(f"Unknown field {name}")

    @classmethod
    def from_bytes(cls, data: typing.Union[bytes, BytesIO]):
        if isinstance(data, bytes):
            data = BytesIO(data)
        return cls(**{field.name: field.type.from_bytes(data) for field in cls.__fields__.values()})

    def to_bytes(self) -> bytes:
        data = []
        for field in type(self).__fields__.values():
            try:
                value = getattr(self, field.name)
            except AttributeError:
                raise ValueError(f"Field '{field.name}' in struct {type(self).__name__} is not initialized") from None
            data.append(field.type.to_bytes(value))
        return b"".join(data)

    def __repr__(self) -> str:
        return str({field: getattr(self, field, None) for field in type(self).__fields__})


__all__ = [
    "DataStruct"
]
