from quickstruct.common import *
from quickstruct.struct_builder import *


def test_alignment():
    struct = FixedStructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields()

    fields = struct.build()

    assert fields["name"].offset == 0
    assert fields["age"].offset == 10
    assert fields["salary"].offset == 16

    assert struct.size == 24


def test_alignment2():
    struct = FixedStructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields()

    fields = struct.build()

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_reordering():
    struct = FixedStructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.reorder_fields()

    fields = struct.build()

    assert fields["name"].offset == 0
    assert fields["salary"].offset == 10
    assert fields["age"].offset == 18

    assert struct.size == 19


def test_reordering2():
    struct = FixedStructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.reorder_fields()

    fields = struct.build()

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligning_reordered():
    struct = FixedStructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.reorder_fields()
    struct.align_fields()

    fields = struct.build()

    assert fields["name"].offset == 0
    assert fields["salary"].offset == 16
    assert fields["age"].offset == 24

    # Actual size: 25. Aligned on 8 bytes.
    assert struct.size == 32


def test_aligning_reordered2():
    struct = FixedStructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.reorder_fields()
    struct.align_fields()

    fields = struct.build()

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_1byte():
    struct = FixedStructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(1)

    fields = struct.build()

    assert fields["name"].offset == 0
    assert fields["age"].offset == 10
    assert fields["salary"].offset == 11

    # Actual size: 19. Aligned on 8 bytes.
    assert struct.size == 24


def test_aligned_on_2bytes():
    struct = FixedStructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(2)

    fields = struct.build()

    assert fields["name"].offset == 0
    assert fields["age"].offset == 10
    assert fields["salary"].offset == 12

    # Actual size: 20. Aligned on 8 bytes.
    assert struct.size == 24


def test_aligned_on_4bytes():
    struct = FixedStructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(4)

    fields = struct.build()

    assert fields["name"].offset == 0
    assert fields["age"].offset == 12
    assert fields["salary"].offset == 16

    assert struct.size == 24


def test_aligned_on_8bytes():
    struct = FixedStructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(8)

    fields = struct.build()

    assert fields["name"].offset == 0
    assert fields["age"].offset == 16
    assert fields["salary"].offset == 24

    assert struct.size == 32


def test_aligned_on_1bytes2():
    struct = FixedStructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(1)

    fields = struct.build()

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_2bytes2():
    struct = FixedStructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(2)

    fields = struct.build()

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_4bytes2():
    struct = FixedStructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(4)

    fields = struct.build()

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_8bytes2():
    struct = FixedStructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(8)

    fields = struct.build()

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 8
    assert fields["e_line"].offset == 16
    assert fields["e_column"].offset == 24

    assert struct.size == 28


def test_align_empty_struct():
    struct = FixedStructBuilder()

    struct.align_fields()

    fields = struct.build()

    assert struct.size == 0
