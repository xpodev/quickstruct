from quickstruct.common import *
from quickstruct.struct_builder import *


def get_fields(struct: StructBuilder):
    return {f.name: f for f in struct.build()}


def test_alignment():
    struct = StructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields()

    fields = get_fields(struct)

    assert fields["name"].offset == 0
    assert fields["age"].offset == 10
    assert fields["salary"].offset == 16

    assert struct.size == 24


def test_alignment2():
    struct = StructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields()

    fields = get_fields(struct)

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_reordering():
    struct = StructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.reorder_fields()

    fields = get_fields(struct)

    assert fields["name"].offset == 0
    assert fields["salary"].offset == 10
    assert fields["age"].offset == 18

    assert struct.size == 19


def test_reordering2():
    struct = StructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.reorder_fields()

    fields = get_fields(struct)

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligning_reordered():
    struct = StructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.reorder_fields()
    struct.align_fields()

    fields = get_fields(struct)

    assert fields["name"].offset == 0
    assert fields["salary"].offset == 16
    assert fields["age"].offset == 24

    assert struct.size == 25


def test_aligning_reordered2():
    struct = StructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.reorder_fields()
    struct.align_fields()

    fields = get_fields(struct)

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_1byte():
    struct = StructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(1)

    fields = get_fields(struct)

    assert fields["name"].offset == 0
    assert fields["age"].offset == 10
    assert fields["salary"].offset == 11

    assert struct.size == 19


def test_aligned_on_2bytes():
    struct = StructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(2)

    fields = get_fields(struct)

    assert fields["name"].offset == 0
    assert fields["age"].offset == 10
    assert fields["salary"].offset == 12

    assert struct.size == 20


def test_aligned_on_4bytes():
    struct = StructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(4)

    fields = get_fields(struct)

    assert fields["name"].offset == 0
    assert fields["age"].offset == 12
    assert fields["salary"].offset == 16

    assert struct.size == 24


def test_aligned_on_8bytes():
    struct = StructBuilder()

    struct.add_field("name", String[10])
    struct.add_field("age", i8)
    struct.add_field("salary", f64)

    struct.align_fields(8)

    fields = get_fields(struct)

    assert fields["name"].offset == 0
    assert fields["age"].offset == 16
    assert fields["salary"].offset == 24

    assert struct.size == 32


def test_aligned_on_1bytes2():
    struct = StructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(1)

    fields = get_fields(struct)

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_2bytes2():
    struct = StructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(2)

    fields = get_fields(struct)

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_4bytes2():
    struct = StructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(4)

    fields = get_fields(struct)

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 4
    assert fields["e_line"].offset == 8
    assert fields["e_column"].offset == 12

    assert struct.size == 16


def test_aligned_on_8bytes2():
    struct = StructBuilder()

    struct.add_field("s_line", i32)
    struct.add_field("s_column", i32)
    struct.add_field("e_line", i32)
    struct.add_field("e_column", i32)

    struct.align_fields(8)

    fields = get_fields(struct)

    assert fields["s_line"].offset == 0
    assert fields["s_column"].offset == 8
    assert fields["e_line"].offset == 16
    assert fields["e_column"].offset == 24

    assert struct.size == 28


def test_align_empty_struct():
    struct = StructBuilder()

    struct.align_fields()

    fields = get_fields(struct)

    assert struct.size == 0
    assert len(fields) == 0
