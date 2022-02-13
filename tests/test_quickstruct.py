from quickstruct import __version__
from quickstruct import *

import pytest

from quickstruct.error import InheritanceError, OverrideError, SizeError, UnoverridbaleFieldError, UnsafeOverrideError


class Person(DataStruct):
    name: String
    _pad0: Padding[1]
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


class Company(DataStruct):
    name: String
    owner: Person
    employees: Array[Employee]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Company):
            return super().__eq__(other)
        return self.name == other.name and self.owner == other.owner and self.employees == other.employees


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
    assert __version__ == '0.1.5'


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

    print(struct)

    assert struct.a == 1
    assert struct.b == 2
    assert struct.size == 16


def test_inheriting_final_struct():
    class FinalStruct(DataStruct, flags=StructFlags.Final):
        a: i16
        b: i32

    def test1():
        class _(FinalStruct):
            c: i32

    def test2():
        class _(Person, FinalStruct):
            c: i32

    with pytest.raises(InheritanceError):
        test1()

    with pytest.raises(InheritanceError):
        test2()


def test_override_struct():
    class _(Person):
        age: i8

    person = _(name="John Doe", age=42)

    assert person.name == "John Doe"
    assert person.age == 42


def test_override_struct_error():
    def test():
        class _(Person, flags=StructFlags.Default & ~StructFlags.AllowOverride):
            age: i8

    with pytest.raises(OverrideError):
        test()


def test_override_struct_safe():
    class _(Person, flags=StructFlags.TypeSafeOverride):
        age: i8

    person = _(name="John Doe", age=42)

    assert person.name == "John Doe"
    assert person.age == 42


def test_override_struct_safe_error():
    def test():
        class _(Person, flags=StructFlags.TypeSafeOverride):
            age: i16 # original type: i8

    with pytest.raises(UnsafeOverrideError):
        test()


def test_locked_structure_override():
    class LockedStruct(DataStruct, flags=StructFlags.LockedStructure):
        a: i16
        b: i32

    def test():
        class _(LockedStruct):
            a: i16

    with pytest.raises(UnoverridbaleFieldError):
        test()


def test_force_fixed_size_struct():
    class Fixed(DataStruct, flags=StructFlags.FixedSize):
        a: i16
        b: i32
        c: String[10]

    assert Fixed.is_fixed_size


def test_force_fixed_size_struct_error():
    def test():
        class _(DataStruct, flags=StructFlags.FixedSize):
            a: i16
            b: i32
            c: String

    with pytest.raises(SizeError):
        test()


def test_composed_struct():
    company = Company(name="Acme", owner=Person(name="John Doe", age=42), employees=[
        Employee(name="Jane Doe", age=32, salary=123.45),
        Employee(name="John Smith", age=42, salary=123.45),
    ])

    assert company.name == "Acme"
    assert company.owner.name == "John Doe"
    assert company.owner.age == 42

    assert len(company.employees) == 2
    assert company.employees[0].name == "Jane Doe"
    assert company.employees[0].age == 32
    assert company.employees[0].salary == 123.45

    assert company.employees[1].name == "John Smith"
    assert company.employees[1].age == 42
    assert company.employees[1].salary == 123.45

    data = company.to_bytes()
    result = Company.from_bytes(data)

    assert company == result
