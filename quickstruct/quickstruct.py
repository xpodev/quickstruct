from abc import ABCMeta, abstractmethod
from io import BytesIO
import pprint
from struct import Struct, pack, unpack
import typing


U = typing.TypeVar('U')


class TypeMeta(ABCMeta):
    def __repr__(self) -> str:
        if hasattr(self, '__class_repr__'):
            return self.__class_repr__()
        if hasattr(self, '__class_str__'):
            return self.__class_str__()
        return self.__name__
    
    def __instancecheck__(cls, value) -> bool:
        return cls.__is_instance__(value)


class Type(typing.Generic[U], metaclass=TypeMeta):   
    def __class_getitem__(cls: typing.Type[U], item) -> "typing.Type[Array[U]]":
        if isinstance(item, int):
            if issubclass(cls, Padding):
                return type(f"Padding({item})", (cls,), {
                    "__struct__": Struct(f"{item}x"),
                })
            return _array(cls, item)
        return super().__class_getitem__(item)

    @classmethod
    @abstractmethod
    def to_bytes(cls: typing.Type[U], data: U) -> bytes:...

    @classmethod
    @abstractmethod
    def from_bytes(cls: typing.Type[U], data: typing.Union[bytes, BytesIO]) -> U:...

    @classmethod
    @abstractmethod
    def __is_instance__(cls, instance) -> bool:...        


T = typing.TypeVar('T', covariant=True, bound=Type)


class Primitive(Type, typing.Generic[T]):
    __struct__: Struct
    __type__: typing.Type[T]
    
    @classmethod
    def to_bytes(cls, data: T) -> bytes:
        return cls.__struct__.pack(data)

    @classmethod
    def from_bytes(cls, data: typing.Union[bytes, BytesIO]) -> T:
        if isinstance(data, bytes):
            data = BytesIO(data)
        return cls.__struct__.unpack(data.read(cls.__struct__.size))[0]

    @classmethod
    def __is_instance__(cls, instance) -> bool:
        return isinstance(instance, cls.__type__)

    def __str__(self) -> str:
        return self.__class__.__name__


class Padding(Primitive[None]):
    __struct__: Struct = Struct("x")

    @classmethod
    def to_bytes(cls, _) -> bytes:
        return cls.__struct__.pack()

    @classmethod
    def from_bytes(cls, data: typing.Union[bytes, BytesIO]) -> T:
        if isinstance(data, bytes):
            data = BytesIO(data)
        return cls.__struct__.unpack(data.read(cls.__struct__.size))[0]


class String(Type):
    __length__: int = None

    @classmethod
    def to_bytes(cls, data: str) -> bytes:
        if not cls.__length__:
            return pack(f"i {len(data)}s", len(data), data.encode())
        return cls.__struct__.pack(data.encode())

    @classmethod
    def from_bytes(cls, data: typing.Union[bytes, BytesIO]) -> str:
        length = cls.__length__
        if isinstance(data, bytes):
            data = BytesIO(data)
        if not length:
            length = unpack("i", data.read(4))[0]
        return data.read(length).decode()
    
    @classmethod
    def __is_instance__(cls, instance) -> bool:
        return isinstance(instance, str)

    def __class_getitem__(cls, item: int) -> typing.Type["String"]:
        if not isinstance(item, int):
            raise TypeError(f"Expected an int, got {item}")
        return type(f"{cls.__name__}[{item}]", (String,), {
            '__length__': item,
            '__struct__': Struct(str(item) + "s"),
            })

    @classmethod
    def __class_str__(cls) -> str:
        if not cls.__length__:
            return "String"
        return f"String[{cls.__length__}]"


class Array(Type, typing.Generic[T]):
    __element_type__: T
    __length__: int = None

    @classmethod
    def to_bytes(cls, values: typing.Iterable[T]) -> bytes:
        if cls.__length__ and len(values) != cls.__length__:
            raise ValueError(f"Expected {cls.__length__} elements, got {len(values)}")
        result = b"".join(cls.__element_type__.to_bytes(value) for value in values)
        if not cls.__length__:
            result = pack(f"i", len(values)) + result
        return result

    @classmethod
    def from_bytes(cls, data: typing.Union[bytes, BytesIO]) -> typing.List[T]:
        length = cls.__length__
        if isinstance(data, bytes):
            data = BytesIO(data)
        if not length:
            length = unpack("i", data.read(4))[0]
        return [cls.__element_type__.from_bytes(data) for _ in range(length)]

    @classmethod
    def __is_instance__(cls, instance) -> bool:
        return all(isinstance(value, cls.__element_type__) for value in instance)

    def __class_getitem__(cls, item: typing.Type[T]) -> typing.Type["Array[T]"]:
        return type(f"Array[{item.__name__}]", (Array,), {
            '__element_type__': item,
            '__length__': None,
            })


class Pointer(Primitive, typing.Generic[T]):
    __element_type__: T
    __struct__: Struct = Struct("P")
    
    @classmethod
    def to_bytes(cls, value) -> bytes:
        return cls.__struct__.pack(value)

    @classmethod
    def from_bytes(cls, data) -> T:
        if isinstance(data, bytes):
            data = BytesIO(data)
        return cls.__element_type__.from_bytes(data)

    @classmethod
    def __str__(cls) -> str:
        return f"{cls.__element_type__}*"


class Reference(Primitive, typing.Generic[T]):
    __element_type__: T
    __struct__: Struct = Struct("P")
    
    @classmethod
    def to_bytes(cls, value) -> bytes:
        return cls.__struct__.pack(value)

    @classmethod
    def from_bytes(cls, data) -> T:
        if isinstance(data, bytes):
            data = BytesIO(data)
        return cls.__element_type__.from_bytes(data)

    @classmethod
    def __str__(cls) -> str:
        return f"{cls.__element_type__}&"


class DataStruct(Type):
    __fields__: typing.Dict[str, typing.Type[Type]] = {}
    __num_paddings__: int

    def __init__(self, **kwargs) -> None:
        super().__init__()
        try:
            for name, value in kwargs.items():
                if not isinstance(value, self.__fields__[name]):
                    raise TypeError(f"Expected {self.__fields__[name]}, got {type(value)}")
                setattr(self, name, value)
        except KeyError:
            raise TypeError(f"Unknown field {name}")

    def __init_subclass__(cls):
        cls.__fields__ = {}
        for base in cls.__bases__:
            if not issubclass(base, Type): continue
            cls.__fields__.update(base.__fields__)
        for name, typ in cls.__annotations__.items():
            if not issubclass(typ, Type):
                raise TypeError(f"{name} in {cls} is not a Type")
            cls.__fields__[name] = typ
        cls.__slots__ = cls.__fields__.keys()

    @classmethod
    def from_bytes(cls: typing.Type[T], data: typing.Union[bytes, BytesIO]) -> T:
        result = cls()
        if isinstance(data, bytes):
            data = BytesIO(data)
        for field, ftype in cls.__fields__.items():
            value = ftype.from_bytes(data)
            setattr(result, field, value)
        return result

    def to_bytes(self) -> bytes:
        try:
            return b"".join(
                typ.to_bytes(getattr(self, field, None)) for field, typ in self.__fields__.items()
                )
        except AttributeError:
            raise ValueError(f"One of the fields is not initialized") from None

    @classmethod
    def __is_instance__(cls, instance) -> bool:
        return type.__instancecheck__(cls, instance)

    @classmethod
    def __class_str__(cls) -> str:
        if not cls.__fields__:
            return "{}"
        return pprint.pformat(cls.__fields__)

    def __repr__(self) -> str:
        if not self.__fields__:
            return "{}"
        return pprint.pformat({
            field: getattr(self, field, None) for field in self.__fields__
        })


def _array(element_type: typing.Type[T], length: int) -> typing.Type[Array[T]]:
    return type(f"{element_type.__name__}[{length}]", (Array,), {
        '__element_type__': element_type,
        '__length__': length,
    })


def _pointer(element_type: typing.Type[T]) -> typing.Type[Pointer[T]]:
    return type(f"{element_type.__name__}*", (Pointer,), {'__element_type__': element_type})


def _primitive(name: str, fmt: str, typ: typing.Type[T]) -> typing.Type[Primitive[T]]:
    return type(name, (Primitive,), {
        '__struct__': Struct(fmt), 
        '__type__': typ
        })


def _reference(element_type: typing.Type[T]) -> typing.Type[Reference[T]]:
    return type(f"{element_type.__name__}&", (Reference,), {'__element_type__': element_type})


class TypeModifier(typing.Generic[T]):
    def __init__(self, func) -> None:
        self._func = func

    def __getitem__(self, item):
        return self._func(item)


ptr = TypeModifier[Pointer](_pointer)
ref = TypeModifier[Reference](_reference)


i8 = _primitive("i8", "b", int)
u8 = _primitive("u8", "B", int)
i16 = _primitive("i16", "h", int)
u16 = _primitive("u16", "H", int)
i32 = _primitive("i32", "i", int)
u32 = _primitive("u32", "I", int)
i64 = _primitive("i64", "q", int)
u64 = _primitive("u64", "Q", int)
f32 = _primitive("f32", "f", float)
f64 = _primitive("f64", "d", float)
anyptr = _primitive("anyptr", "P", int)
char = _primitive("char", "c", bytes)


__all__ = [
    "i8", "u8", "i16", "u16", "i32", "u32", "i64", "u64", "f32", "f64", "String", 
    "anyptr", "char", "ptr", "ref",
    "Array", "Pointer", "Reference", "DataStruct", "Padding",
]
