from .common import *
from .common import Padding
from .struct_builder import FieldInfo, FixedStructBuilder, DynamicStructBuilder, IStructBuilder, StructFlags

from io import BytesIO
import pprint
import typing


class StructField:
    _type: typing.Type[Type]
    _name: str

    def __init__(self, typ: typing.Type[Type]) -> None:
        self._type = typ

    def __set_name__(self, owner, name):
        self._name = f"<field>_{name}"
        setattr(owner, name, self)

    def __get__(self, instance, _):
        if instance is None:
            return self
        return getattr(instance, self._name)

    def __set__(self, instance, value):
        if not isinstance(value, self._type):
            raise TypeError(f"Expected {self._type}, got {type(value)}")
        setattr(instance, self._name, value)


class DataStruct(Type):
    """Base type for all data structures."""

    __s_fields__: typing.Dict[str, typing.Type[Type]]
    __s_flags__: StructFlags = StructFlags.Default
    __s_size__: int
    __s_alignment__: int

    def __init__(self, **kwargs) -> None:
        super().__init__()
        try:
            for name, value in kwargs.items():
                # if not isinstance(value, self.__fields__[name]):
                #     raise TypeError(f"Expected {self.__fields__[name]}, got {type(value)}")
                setattr(self, name, value)
        except KeyError:
            raise TypeError(f"Unknown field {name}")

    def __init_subclass__(cls, flags: StructFlags = StructFlags.Default):
        if any(map(lambda base: issubclass(base, DataStruct) and base.__s_flags__ & StructFlags.Final, cls.__bases__)):
            raise TypeError("Cannot inherit from a final struct")
        builder: IStructBuilder
        if flags & StructFlags.ForceFixedSize:
            builder = FixedStructBuilder(flags)
        else:
            builder = DynamicStructBuilder(flags)        
        if flags & StructFlags.ForceFixedSize:
            if flags & StructFlags.ReorderFields:
                builder.reorder_fields()
            if not flags & StructFlags.NoAlignment:
                builder.align_fields()
        
        potential_fields: typing.List[FieldInfo] = []

        if flags & StructFlags.ForceDataOnly:
            if any(map(lambda base: not issubclass(base, DataStruct) or not base.__s_flags__ & StructFlags.ForceDataOnly, cls.__bases__)):
                raise TypeError(f"{cls.__name__} is marked as data-only but it inherits non-data-only struct.")

        paddings = 0
        for i, base in enumerate(cls.__bases__):
            if not issubclass(base, DataStruct) or base is DataStruct: continue
            if base.__s_flags__ & StructFlags.AllowInline:
                for name, typ in base.__s_fields__.items():
                    if issubclass(typ, Padding):
                        name = f"<padding>_{paddings}"
                        paddings += 1
                    potential_fields.append(FieldInfo(name, typ))
            else:
                potential_fields.append(FieldInfo(f"<base>_{i}", base))
        
        non_data_fields = []
        
        for name, typ in cls.__annotations__.items():
            if name.startswith('__') and name.endswith('__'): continue
            if issubclass(typ, DataStruct):
                if not typ.__s_flags__ & StructFlags.ForceDataOnly:
                    non_data_fields.append(name)
            if issubclass(typ, Type):
                potential_fields.append(FieldInfo(name, typ))
            else:
                non_data_fields.append(name)

        # for name, value in vars(cls).items():
        #     if name.startswith('__') and name.endswith('__'): continue
        #     typ = type(value)
        #     if issubclass(typ, DataStruct):
        #         if not typ.__s_flags__ & StructFlags.ForceDataOnly:
        #             non_data_fields.append(name)
        #     if issubclass(typ, Type):
        #         potential_fields.append(FieldInfo(name, type(value)))
        #     else:
        #         non_data_fields.append(name)

        if flags & StructFlags.ForceDataOnly and non_data_fields:
            raise TypeError(f"{cls.__name__} is marked as data-only but it contains non-data-only fields: {non_data_fields}.")
        
        for field in potential_fields:
            builder.add_field(field, allow_overwrite=flags & StructFlags.AllowOverride, force_safe_overwrite=flags & StructFlags.ForceSafeOverride)

        fields = builder.build()
        if builder.size != -1:
            builder = FixedStructBuilder(flags)
            for field in fields.values():
                builder.add_field(field, allow_overwrite=flags & StructFlags.AllowOverride, force_safe_overwrite=flags & StructFlags.ForceSafeOverride)
            if flags & StructFlags.ReorderFields:
                builder.reorder_fields()
            if not flags & StructFlags.NoAlignment:
                builder.align_fields()
        fields = builder.build()

        for name, field in fields.items():
            value = getattr(cls, name, None)
            StructField(field.type).__set_name__(cls, name)
            if value is not None:
                setattr(cls, name, value)
        cls.__s_fields__ = {name: field.type for name, field in fields.items()}
        cls.__s_flags__ = flags
        cls.__s_size__ = builder.size
        cls.__s_alignment__ = 0
        cls.__slots__ = fields.keys()

    @classmethod
    def size(cls):
        cls.__s_size__

    @classmethod
    def alignment(cls) -> int:
        return cls.__s_alignment__

    @classmethod
    def from_bytes(cls: typing.Union[typing.Type[T], "DataStruct"], data: typing.Union[bytes, BytesIO]) -> T:
        result = cls()
        if isinstance(data, bytes):
            data = BytesIO(data)
        for field, ftype in cls.__s_fields__.items():
            value = ftype.from_bytes(data)
            setattr(result, field, value)
        return result

    def to_bytes(self) -> bytes:
        try:
            return b"".join(
                typ.to_bytes(getattr(self, field, None)) for field, typ in self.__s_fields__.items()
                )
        except AttributeError:
            raise ValueError(f"One of the fields is not initialized") from None

    @classmethod
    def __is_instance__(cls, instance) -> bool:
        return type.__instancecheck__(cls, instance)

    @classmethod
    def __class_str__(cls) -> str:
        if not cls.__s_fields__:
            return "{}"
        return pprint.pformat(cls.__s_fields__)

    def __repr__(self) -> str:
        if not self.__s_fields__:
            return "{}"
        return pprint.pformat({
            field: getattr(self, field, None) for field in self.__s_fields__
        })


__all__ = [
    "DataStruct"
]
