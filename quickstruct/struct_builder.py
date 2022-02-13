from abc import ABC, abstractmethod
from enum import IntFlag
import typing

from .common import Primitive, Type, Padding
from .field import FieldInfo
from .utils import deprecated

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
    """
    [DEPRECATED] If set, the struct may only contain fields of serializable types. Data-only structs may only inherit other data-only structs.
    This flag is no longer used and will be removed in the next major version
    """

    AllowOverride = 1 << 9
    """If set, the struct may contain fields that are defined in the base struct."""
    TypeSafeOverride = 1 << 10 | AllowOverride
    """If set, the struct may only define fields that are defined in the base struct with the same type."""
    ForceSafeOverride = TypeSafeOverride
    """
    [DEPRECATED] Same as SafeOverride.
    """

    FixedSize = 1 << 11
    """If set, the struct will be forced to have a fixed size. If a fixed size could not be determined, an exception `SizeError` will be raised."""
    ForceFixedSize = FixedSize
    """
    [DEPRECATED] Same as FixedSize. This flag is no longer used and will be removed in the next major version. Use FixedSize instead.
    """

    AllowInline = 1 << 13
    """
    [DEPRECATED ]If set, the struct may be unpacked into another struct. 
    This flag is no longer used and will be removed in the next major version.
    In order to inline a struct, inherit from it instead.
    """

    Protected = 1 << 14
    """If set, the fields of the struct may not be overridden and can't be aligned or reordered."""
    LockedStructure = Protected
    """[DEPRECATED] Same as Protected. Use Protected instead. This will be removed in next major version."""

    Final = 1 << 15
    """If set, the struct may not be inherited."""


    AlignmentMask = Align1Byte | Align2Bytes | Align4Bytes | Align8Bytes
    """The mask for the alignment power."""
    Default = AllowOverride | AlignAuto
    """The default flags for a struct. This is equivalent to AllowOverride | AlignAuto."""


class IStructBuilder(ABC):
    """[DEPRECATED] This class is no longer used. Use StructBuilder instead."""

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


@deprecated("No longer used (This was internal API anyway). Use StructBuilder instead.")
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
            size = field.type._size()
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


@deprecated("No longer used (This was internal API anyway). Use StructBuilder instead.")
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
        if field.type._is_dynamic_size():
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
                size = field.type._size()
                if issubclass(field.type, Primitive):
                    largest_field = max(largest_field, size)
                offset += size + padding
                result.append(field)
        else:
            for field in self._fields.values():
                padding = self.__get_padding(field.type._alignment(), offset)
                if padding:
                    result.append(FieldInfo(f"<padding>_{paddings}", Padding[padding]))
                    paddings += 1
                size = field.type._size()
                if issubclass(field.type, Primitive):
                    largest_field = max(largest_field, size)
                offset += size + padding
                result.append(field)
        self._size = offset
        self._fields = {field.name: field for field in result}
        if self._size and self._size % largest_field != 0:
            self._size += largest_field - (self._size % largest_field)

    def reorder_fields(self) -> None:
        fields_by_sizes: Dict[int, List[FieldInfo]] = {}
        for field in self._fields.values():
            size = field.type._size()
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
            offset += field.type._size()

    def __get_padding(self, alignment: int, offset: int) -> int:
        return -offset & (alignment - 1)

    def build(self) -> Dict[str, FieldInfo]:
        self.recalculate_alignments()
        return self._fields

    @property
    def size(self) -> int:
        return self._size


class StructBuilder:
    _pad_format: str = "__pad_{}__"

    _fields: List[FieldInfo]
    _size: int
    _has_dynamic_fields: bool

    def __init__(self) -> None:
        self._fields = []
        self._size = 0
        self._has_dynamic_fields = False

    def add_field(self, field: Union[str, FieldInfo], typ = None) -> None:
        if isinstance(field, str):
            field = FieldInfo(field, typ)
        self._has_dynamic_fields |= field.type.is_dynamic_size
        self._fields.append(field)

    def align_fields(self, alignment: int = None) -> None:
        if not self._fields or self._has_dynamic_fields:
            return
        if alignment:
            self.__align_fields_by_alignment(alignment)
            self.__pad_to_alignment(alignment)
        else:
            self.__align_fields_by_type()
            self.__pad_to_alignment(max(field.type.alignment for field in self._fields))

    def reorder_fields(self) -> None:
        sized_fields: List[FieldInfo] = []
        dynamic_fields: List[FieldInfo] = []
        for field in self._fields:
            if field.type.is_dynamic_size:
                dynamic_fields.append(field)
            else:
                sized_fields.append(field)
        # todo: pack fields so they are compressed as much as possible
        self._fields = sorted(sized_fields, key=lambda field: field.type.size, reverse=True) + dynamic_fields

    def __align_fields_by_alignment(self, alignment: int) -> None:
        result: List[FieldInfo] = []
        paddings = offset = 0
        for field in self._fields:
            padding = self.__get_padding(alignment, offset)
            if padding:
                result.append(FieldInfo(self._pad_format.format(paddings), Padding[padding]))
                paddings += 1
            size = field.type.size
            offset += size + padding
            result.append(field)
        self._fields = result

    def __align_fields_by_type(self) -> None:
        result: List[FieldInfo] = []
        paddings = offset = 0
        for field in self._fields:
            padding = self.__get_padding(field.type.alignment, offset)
            if padding:
                result.append(FieldInfo(self._pad_format.format(paddings), Padding[padding]))
                paddings += 1
            size = field.type.size
            offset += size + padding
            result.append(field)
        self._fields = result

    def __get_padding(self, alignment: int, offset: int) -> int:
        return -offset & (alignment - 1)

    def __pad_to_alignment(self, alignment: int) -> None:
        if self.is_dynamic_size:
            return
        padding = self.__get_padding(alignment, self._size)
        if padding:
            self._fields.append(FieldInfo(self._pad_format.format(""), Padding[padding]))

    def __recalculate_offsets(self) -> None:
        offset = 0
        for field in self._fields:
            field.offset = offset
            offset += field.type.size

    def __recalculate_size(self) -> None:
        if self._has_dynamic_fields:
            self._size = -1
            return
        size = 0
        for field in self._fields:
            size += field.type.size
        self._size = size

    def build(self) -> List[FieldInfo]:
        self.__recalculate_offsets()
        self.__recalculate_size()
        return self._fields

    @property
    def size(self) -> int:
        return self._size

    @property
    def is_dynamic_size(self) -> bool:
        return self._has_dynamic_fields or self.size == -1
