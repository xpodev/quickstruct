from quickstruct import __version__
from quickstruct import *

import pytest


class Person(DataStruct):
    name: String
    age: i8

    def __eq__(self, other: "Person") -> bool:
        return self.name == other.name and self.age == other.age


class Employee(Person):
    salary: f64

    def __eq__(self, other: "Employee") -> bool:
        if isinstance(other, Employee):
            return super().__eq__(other) and self.salary == other.salary
        else:
            return super().__eq__(other)


class PackedStruct1(DataStruct, flags=StructFlags.Align1Byte):
    a: i16
    b: i32
    size: i32 = 10


class PackedStruct2(DataStruct, flags=StructFlags.Align2Bytes):
    a: i16
    b: i32
    size: i32 = 10


class PackedStruct4(DataStruct, flags=StructFlags.Align4Bytes):
    a: i16
    b: i32
    size: i32 = 12


class PackedStruct8(DataStruct, flags=StructFlags.Align8Bytes):
    a: i16
    b: i32
    size: i32 = 16


def test_version():
    assert __version__ == '0.1.2'


def test_struct_data():
    person = Person(name="John Doe", age=42)

    assert person.name == "John Doe"
    assert person.age == 42


def test_struct_inheritance():
    employee = Employee(name="John Doe", age=42, salary=123.45)

    assert employee.name == "John Doe"
    assert employee.age == 42
    assert employee.salary == 123.45


def test_struct_serialization():
    person = Person(name="John Doe", age=42)

    data = person.to_bytes()
    result = Person.from_bytes(data)

    assert person == result


def test_struct_inheritance_serialization():
    employee = Employee(name="John Doe", age=42, salary=123.45)

    data = employee.to_bytes()
    result = Person.from_bytes(data)

    assert employee == result

    result = Employee.from_bytes(data)
    assert employee == result


def test_struct_set_field():
    person = Person(name="John Doe", age=42)
    person.age = 43

    assert person.age == 43

    with pytest.raises(TypeError):
        person.age = "42"

    with pytest.raises(TypeError):
        person.age = 42.0

    with pytest.raises(TypeError):
        person.age = None


def test_aligned_struct1():
    struct = PackedStruct1(a=1, b=2)

    assert struct.a == 1
    assert struct.b == 2
    assert struct.size == 10


def test_aligned_struct2():
    struct = PackedStruct2(a=1, b=2)

    assert struct.a == 1
    assert struct.b == 2
    assert struct.size == 10


def test_aligned_struct4():
    struct = PackedStruct4(a=1, b=2)

    assert struct.a == 1
    assert struct.b == 2
    assert struct.size == 12


def test_aligned_struct8():
    struct = PackedStruct8(a=1, b=2)

    assert struct.a == 1
    assert struct.b == 2
    assert struct.size == 16
