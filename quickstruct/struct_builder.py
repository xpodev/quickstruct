from abc import ABC, abstractmethod
from enum import IntFlag
import typing
from .common import Primitive, Type, Padding

from typing import Dict, List, Union


class StructFlags(IntFlag):
    Align1Byte = Packed = 0
    """Specifies the struct should not be aligned."""
    Align2Bytes = 1 << 0
    """Specifies the struct should be aligned to 2 bytes."""
    Align4Bytes = 1 << 1
    """Specifies the struct should be aligned to 4 bytes."""
    Align8Bytes = 1 << 2
    """Specifies the struct should be aligned to 8 bytes."""
    AlignAuto = 1 << 3
    """Specifies the alignment should be automatically determined by the field types."""
    NoAlignment = 1 << 4
    """Specifies the struct should not be aligned."""
    ReorderFields = 1 << 5
    """If set, the fields will be reordered to fill the gaps in the struct. Reordering implies alignment."""
    ForceDataOnly = 1 << 8
    """If set, the struct may only contain fields of serializable types. Data-only structs may only inherit other data-only structs."""
    AllowOverride = 1 << 9
    """If set, the struct may contain fields that are defined in the base struct."""
    ForceSafeOverride = 1 << 10
    """If set, the struct may only define fields that are defined in the base struct with the same type."""
    ForceFixedSize = 1 << 11
    """If set, the struct will be forced to have a fixed size. If a fixed size could not be determined, an exception will be raised."""
    AllowInline = 1 << 13
    """If set, the struct may be unpacked into another struct."""
    LockedStructure = 1 << 14
    """If set, the fields of the struct may not be overridden and can't be aligned or reordered."""
    Final = 1 << 15
    """If set, the struct may not be inherited."""

    AlignmentMask = Align1Byte | Align2Bytes | Align4Bytes | Align8Bytes
    """The mask for the alignment power."""
    Default = AllowOverride | AlignAuto | ForceDataOnly | AllowInline
    """The default flags for a struct. This is equivalent to AllowOverride | Packed | ForceDataOnly | AllowInline."""


class FieldInfo:
    _name: str
    _type: Type
    _offset: int

    def __init__(self, name: str, typ: Type) -> None:
        if name is None:
            raise TypeError("Field name must not be None")
        if typ is None:
            raise TypeError("Field type must not be None")
        self._name = name
        self._type = typ
        self._offset = 0

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


class IStructBuilder(ABC):
    @abstractmethod
    def add_field(self, field: FieldInfo, allow_overwrite: bool = True, force_safe_overwrite: bool = True) -> None:
        """Adds a field to the struct.
        
        Args:
            field: The name of the field or a FieldInfo object.
            typ: The type of the field.
            allow_overwrite: If True, the field can be overwritten.
            force_safe_overwrite: If True, the field can only be overwritten if the new type is safe to overwrite.
        """
        ...

    @abstractmethod
    def build(self) -> Dict[str, FieldInfo]:
        """Builds the struct."""
        ...


class DynamicStructBuilder(IStructBuilder):
    _fields: Dict[str, FieldInfo]
    _size: int
    _flags: StructFlags

    def __init__(self, flags: StructFlags = StructFlags.Default) -> None:
        self._fields = {}
        self._size = 0
        self._flags = flags

    def add_field(self, field: FieldInfo, allow_overwrite: bool = True, force_safe_overwrite: bool = True) -> None:
        if field.name in self._fields:
            if not allow_overwrite:
                raise ValueError(f"Field '{field.name}' already exists in the struct.")
            if force_safe_overwrite and self._fields[field.name].type != field.type:
                raise ValueError(f"Field '{field.name}' already exists in the struct with a different type.")
        self._fields[field.name] = field
    
    def reclaculate_size(self):
        total_size = 0
        for field in self._fields.values():
            size = field.type.size()
            if size == -1:
                self._size = -1
                return
            total_size += size
        self._size = total_size

    def build(self) -> Dict[str, FieldInfo]:
        self.reclaculate_size()
        return self._fields

    @property
    def size(self) -> int:
        return self._size

    @property
    def is_dynamic(self) -> bool:
        return self._size == -1


class FixedStructBuilder(IStructBuilder):
    _fields: Dict[str, FieldInfo]
    _size: int
    _alignment: int
    _flags: StructFlags

    def __init__(self, flags: StructFlags = StructFlags.Default) -> None:
        self._fields = {}
        self._size = 0
        self._alignment = 1 << (flags & StructFlags.AlignmentMask) if not flags & StructFlags.AlignAuto else 0
        self._flags = flags

    def add_field(self, field: FieldInfo, typ: typing.Type[Type] = None, allow_overwrite: bool = True, force_safe_overwrite: bool = True) -> None:
        if isinstance(field, str):
            field = FieldInfo(field, typ)
        if field.type.is_dynamic_size():
            raise ValueError("Cannot add a dynamic sized field to a fixed struct.")
        if field.name in self._fields:
            if not allow_overwrite:
                raise ValueError(f"Field '{field.name}' already exists in the struct.")
            if force_safe_overwrite and self._fields[field.name].type != field.type:
                raise ValueError(f"Field '{field.name}' already exists in the struct with a different type.")
        self._fields[field.name] = field

    def align_fields(self, alignment: int = None) -> None:
        if alignment is None:
            return self.align_fields(self._alignment)
        result = []
        offset = 0
        paddings = 0
        largest_field = 0
        if alignment:
            for field in self._fields.values():
                padding = self.__get_padding(alignment, offset)
                if padding:
                    result.append(FieldInfo(f"<padding>_{paddings}", Padding[padding]))
                    paddings += 1
                size = field.type.size()
                if issubclass(field.type, Primitive):
                    largest_field = max(largest_field, size)
                offset += size + padding
                result.append(field)
        else:
            for field in self._fields.values():
                padding = self.__get_padding(field.type.alignment(), offset)
                if padding:
                    result.append(FieldInfo(f"<padding>_{paddings}", Padding[padding]))
                    paddings += 1
                size = field.type.size()
                if issubclass(field.type, Primitive):
                    largest_field = max(largest_field, size)
                offset += size + padding
                result.append(field)
        self._size = offset
        self._fields = {field.name: field for field in result}
        if self._size % largest_field != 0:
            self._size += largest_field - (self._size % largest_field)

    def reorder_fields(self) -> None:
        fields_by_sizes: Dict[int, List[FieldInfo]] = {}
        for field in self._fields.values():
            size = field.type.size()
            if size not in fields_by_sizes:
                fields_by_sizes[size] = []
            fields_by_sizes[size].append(field)
        result = []
        offset = 0
        for size in sorted(fields_by_sizes.keys(), reverse=True):
            for field in fields_by_sizes[size]:
                field.offset = offset
                offset += size
                result.append(field)
        self._size = offset
        self._fields = {field.name: field for field in result}

    def recalculate_alignments(self) -> None:
        offset = 0
        for field in self._fields.values():
            field.offset = offset
            offset += field.type.size()

    def __get_padding(self, alignment: int, offset: int) -> int:
        return -offset & (alignment - 1)

    def build(self) -> Dict[str, FieldInfo]:
        self.recalculate_alignments()
        return self._fields

    @property
    def size(self) -> int:
        return self._size
