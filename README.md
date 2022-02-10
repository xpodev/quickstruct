# QuickStruct

QuickStruct is a small library written in Python that allows you to
easily create C structs (and a bit more dynamic stuff) in Python!

It's fairly easy to use
```py
from quickstruct import *

class Person(DataStruct):
    name: String
    age: i8
```

Structs can also be composed

```py
class TeachingClass(DataStruct):
    teacher: Person
    # We use Array[T] to make it dynamic sized
    students: Array[Person]
```

And structs can also inherit other structs
(we even support multiple inheritance!)
```py
class Employee(Person):
    salary: i32
```


Now let's use the structs we defined
```py
# We have 2 options when initializing.
# Either by setting each attribute individually
person = Person()
person.name = "John Doe"
person.age = 42

# Or by passing them as keyword arguments
person = Person(name="John Doe", age=42)
```


The main use for C structs is to convert them from bytes and back
```py
data = person.to_bytes()
# Do something with the data

# And it's also easy to deserialize
person = Person.from_bytes(data)
```


When deserializing a struct with multiple bases or if one of the fields was overriden, 
the deserialization must be done through the exact type of the struct.


# Alignment
It is also possible to add padding to the struct. There are 2 ways to do that:
## Manual Alignment
This can be done with the `Padding` type.
```py
class AlignedStruct(DataStruct):
    c1: char
    # This adds a single byte padding
    _pad0: Padding
    short: i16
    # We can also add multi-byte padding
    # Here we'll pad to get 8 byte alignment (missing 4 bytes)
    _pad1: Padding[4]
```

## Automatic Alignment
This can done by passing some flags to the class definition. By default the struct is automatically aligned.
```py
# Aligned on 2 byte boundary
class AlignedStruct(DataStruct, flags = StructFlags.Align2Bytes):
    c1: char
    # Padding will be added here
    short: i16
```

## Struct Flags
| Flag              | Description                                                                                                           |
|-------------------|-----------------------------------------------------------------------------------------------------------------------|
| NoAlignment       | This is the most packed form of the struct. All fields are adjacent with no padding (unless manually added)           |
| Packed            | Same as `NoAlignment` except that `NoAlignment` is a bit more optimized because no alignment is done.                 |
| Align1Byte        | Same as `Packed`                                                                                                      |
| Align2Bytes       | Aligns the fields on 2 byte boundary.                                                                                 |
| Align4Bytes       | Aligns the fields on 4 byte boundary.                                                                                 |
| Align8Bytes       | Aligns the fields on 8 byte boundary.                                                                                 |
| AlignAuto         | Aligns the fields by their type.                                                                                      |
| ReorderFields     | Specifies the fields should be reordered in order to make the struct a little more compressed.                        |
| ForceDataOnly     | Specifies that the struct may only contain serializable fields. Data-only structs may only inherit data-only structs. |
| AllowOverride     | If set, fields defined in the struct may override fields that are defined in the base struct.                         |
| ForceSafeOverride | If set, when fields are overridden, they must have the same type (which would make it pretty useless to override).    |
| ForceFixedSize    | If set, the struct must have a fixed size. If not, an exception is raised.                                            |
| AllowInline       | If set, the struct's fields will be inlined into another struct the contains this struct.                             |
| Final             | Marks the structure so it won't be inheritable by any other class.                                                    |
| LockedStructure   | If set, denies any overrides of that structure. This flag is not yet implemented.                                     |


