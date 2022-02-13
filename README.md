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


# Fixed Size Structs
A fixed size struct is any struct that has a known fixed time that doesn't depend on the 
data it holds. QuickStruct can verify a struct has a fixed size.
```py
# The StructFlags.FixedSize flag is used to verify the struct has a fixed size.
# If the size could not be verified, a SizeError is raised.
class FixedSizeStruct(DataStruct, flags=StructFlags.FixedSize):
    a: i32
    b: i8
    c: f32
    d: char
    e: String[10] # 10 character string
    f: Person[3] # 3 'person' objects
    # g: Array[i32] <- not a fixed size field. this will error
```

# Struct Properties
It is possible to query some information about a structure.
```py
from quickstruct import *
class Fixed(DataStruct):
    s: String[10]
    x: i32

class Dynamic(DataStruct):
    s: String
    x: i32

print("Fixed.size:", Fixed.size) # 16 (padding automatically added)
print("Dynamic.size:", Dynamic.size) # -1 (dynamic size)

print("Fixed.is_fixed_size:", Fixed.is_fixed_size) # True
print("Dynamic.is_fixed_size:", Fixed.is_fixed_size) # False

print("Fixed.is_dynamic_size:", Fixed.is_dynamic_size) # False
print("Dynamic.is_dynamic_size:", Fixed.is_dynamic_size) # True

print("Fixed.fields:", Fixed.fields) # [s: String[10], __pad_0__: Padding(2), x: i32]
print("Dynamic.fields:", Dynamic.fields) # [s: String, x: i32]

print("Fixed.aligment:", Fixed.aligment) # 16.
print("Dynamic.aligment:", Dynamic.aligment) # -1 (no alignment because dynamic struct can't be aligned).

print("Fixed.is_final:", Fixed.is_final) # False
print("Dynamic.is_final:", Fixed.is_final) # False

print("Fixed.is_protected:", Fixed.is_protected) # False
print("Dynamic.is_protected:", Fixed.is_protected) # False
```

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
| Flag              | Description                                                                                                                                                                                                      |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Default           | The default to use if no flags are given. Same as `AllowOverride \| AlignAuto`.                                                                                                                                  |
| NoAlignment       | This is the most packed form of the struct. All fields are adjacent with no padding (unless manually added)                                                                                                      |
| Packed            | Same as `NoAlignment` except that `NoAlignment` is a bit more optimized because no alignment is done.                                                                                                            |
| Align1Byte        | Same as `Packed`                                                                                                                                                                                                 |
| Align2Bytes       | Aligns the fields on 2 byte boundary.                                                                                                                                                                            |
| Align4Bytes       | Aligns the fields on 4 byte boundary.                                                                                                                                                                            |
| Align8Bytes       | Aligns the fields on 8 byte boundary.                                                                                                                                                                            |
| AlignAuto         | Aligns the fields by their type.                                                                                                                                                                                 |
| ReorderFields     | Specifies the fields should be reordered in order to make the struct a little more compressed.                                                                                                                   |
| ForceDataOnly     | **Deprecated**. Specifies that the struct may only contain serializable fields. Data-only structs may only inherit data-only structs.                                                                            |
| AllowOverride     | If set, fields defined in the struct may override fields that are defined in the base struct.                                                                                                                    |
| TypeSafeOverride  | If set, when fields are overridden, they must have the same type (which would make it pretty useless to override). Implies `AllowOverride`. If fields have a different type, an `UnsafeOverrideError` is raised. |
| ForceSafeOverride | **Deprectaed**. Same as `TypeSafeOverride`.                                                                                                                                                                      |
| FixedSize         | If set, the struct must have a fixed size. If not, an exception `SizeError` is raised.                                                                                                                           |
| ForceFixedSize    | **Deprecated**. Same as `FixedSize`.                                                                                                                                                                             |
| AllowInline       | **Deprecated**. If set, the struct's fields will be inlined into another struct the contains this struct.                                                                                                        |
| Protected         | If set, denies any overrides of that structure. If a struct is trying to override a field of it, an `UnoverridableFieldError` is raised.                                                                         |
| LockedStructure   | **Deprecated**. Same as `Protected`.                                                                                                                                                                             |
| Final             | Marks the structure so it won't be inheritable by any other class. If a struct is trying to inherit it, an `InheritanceError` is raised.                                                                         |