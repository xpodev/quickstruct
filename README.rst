===========
QuickStruct
===========

QuickStruct is a small library written in Python that allows you to
easily create C structs (and a bit more dynamic stuff) in Python!

It's fairly easy to use::

    from quickstruct import *

    class Person(DataStruct):
        name: String
        age: i8

Structs can also be composed::

    class TeachingClass(DataStruct):
        teacher: Person
        # we use Array[T] to make it dynamic sized
        students: Array[Person]


And structs can also inherit other structs
(we even support multiple inheritance!)::

    class Employee(Person):
        salary: i32


Now let's use the structs we defined::

    # we have 2 options when initializing
    # 1. by setting each attribute individually
    person = Person()
    person.name = "John Doe"
    person.age = 42

    # or by passing them as keyword arguments
    person = Person(name="John Doe", age=42)


The main use for C structs is to convert them from bytes and back::

    data = person.to_bytes()
    # do something with the data
    
    # and it's also easy to deserialize
    person = Person.from_bytes(data)


When deserializing a struct with multiple bases or if one of the fields was overriden, 
the deserialization must be done through the exact type of the struct.
