import random

from qa_tool.utils.utils import ClassPropertyDescriptor


class Enum:

    @classmethod
    def as_dict(cls, matcher=None):
        matcher = matcher or (lambda value: True)
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith("_")
            and not isinstance(value, classmethod)
            and matcher(value)
            and not isinstance(value, ClassPropertyDescriptor)
        }

    @classmethod
    def get_random(cls, matcher=None):
        return random.choice(cls.get_all(matcher=matcher))

    @classmethod
    def get_all(cls, matcher=None):
        return sorted(cls.as_dict(matcher=matcher).values())


if __name__ == '__main__':
    from qa_tool.utils.utils import classproperty

    class Keks(Enum):
        qwe = 'qwe'
        qweq = 'qweq'

        @classproperty
        def sad(self):
            return 'asdxzc'

    print(Keks.get_all())
    qweqweqw = Keks.sad
    print(qweqweqw)