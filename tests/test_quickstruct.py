from quickstruct import __version__
from quickstruct import *


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
