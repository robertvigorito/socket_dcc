import dataclasses


@dataclasses.dataclass(eq=True, frozen=True)
class Number:
    value: int

    def __add__(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value)
        raise TypeError("unsupported operand type(s) for +: 'Number' and 'Number'")



one = Number(1)

two = Number(2)
print(one + two)  # TypeError: unsupported operand type(s) for +: 'Number' and 'Number'

print(one != two)  # False
