'''
Лабораторная работа 4 (валидация и автообновление через события)

Реализуем паттерн Broadcaster/receiver или observer, симулируем событийное программирование.
1. Создать протокол/интерфейс EventHandler<TEventArgs>
 - handle(sender: object (or Any), args: TEventArgs) для обработки события
где TEventArgs - произвольный тип данных

2. Создать класс Event, который реализует механизм подписки и отписки от события, а также оповещение всех подписантов
  - "+=" (handler: EventHandler<TEventArgs>) - подписка на событие
  - "-="  (handler: EventHandler<TEventArgs>)  - отписка от события
  - invoke(sender: T,  args: TEventArgs) (в Python можно вместо нее или дополнительно использовать call) - запускает оповещение всех подписантов

3. Создать класс PropertyChangedEventArgs(EventArgs)
  - свойство property_name: str

4. Создать класс реализующий EventHandler<PropertyChangedEventArgs>, обрабатывающий событие и выводящий информацию в консоль

5. Создать класс PropertyChangingEventArgs(EventArgs)
  - свойство property_name: str
  - свойство old_value: Any
  - свойство new_value: Any
  - свойство can_change: bool

6. Создать класс реализующий EventHandler<PropertyChangingEventArgs>, обрабатывающий событие и работающий как валидатор при попытке изменения свйоства.
Для отмены измененения используйте свйоство can_change

7. Создать не менее двух классов, каждый из которых имеет не менее трех полей, которые при изменении свойств вызывают событие от EventHandler<PropertyChangedEventArgs> после изменения свойства и
EventHandler<PropertyChangingEventArgs> до изменения значения свойства с возможностью отменить изменение
'''

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Optional, TypeVar, Generic

# Базовые типы для событий
TEventArgs = TypeVar('TEventArgs')


class EventHandler(ABC, Generic[TEventArgs]):
    '''Класс обработчика события'''

    @abstractmethod
    def handle(self, sender: object, args: TEventArgs) -> None:
        '''Обработать событие'''
        pass


class EventArgs:
    '''Класс для аргументов события'''
    pass


# Управление подпиской и оповещением
class Event(Generic[TEventArgs]):
    '''механизм подписки на событие и его вызов'''

    def __init__(self) -> None:
        self._handlers: List[EventHandler[TEventArgs]] = []

    def __iadd__(self, handler: EventHandler[TEventArgs]) -> 'Event[TEventArgs]':
        '''Подписка на событие (+=)'''
        if handler not in self._handlers:
            self._handlers.append(handler)
        return self

    def __isub__(self, handler: EventHandler[TEventArgs]) -> 'Event[TEventArgs]':
        '''Отписка от события (-=)'''
        if handler in self._handlers:
            self._handlers.remove(handler)
        return self

    def __call__(self, sender: object, args: TEventArgs) -> None:
        '''Оповещение всех подписчиков'''
        for handler in self._handlers:
            handler.handle(sender, args)


# Аргументы для событий изменения свойств
class PropertyChangedEventArgs(EventArgs):
    '''Аргументы события после изменения свойства'''

    def __init__(self, property_name: str) -> None:
        self.property_name = property_name


class PropertyChangingEventArgs(EventArgs):
    '''Аргументы события до изменения свойства'''

    def __init__(self, property_name: str, old_value: Any, new_value: Any) -> None:
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.can_change = True  # изменение разрешено (по умолчанию)


# Конкретные обработчики событий
class ConsolePropertyChangedHandler(EventHandler[PropertyChangedEventArgs]):
    '''Вывод информации в консоль'''

    def handle(self, sender: object, args: PropertyChangedEventArgs) -> None:
        print(f"Свойство '{args.property_name}' объекта {sender} изменено.")


class ValidatingPropertyChangingHandler(EventHandler[PropertyChangingEventArgs]):
    '''Валидация с возможностью отмены'''

    def __init__(self, forbidden_values: Optional[List[Any]] = None) -> None:
        self.forbidden_values = forbidden_values if forbidden_values is not None else []

    def handle(self, sender: object, args: PropertyChangingEventArgs) -> None:
        new_val = args.new_value

        for item in self.forbidden_values:

            if not isinstance(item, tuple) and new_val == item:  # Попадание
                print(f"Изменение свойств '{args.property_name}' на {new_val}")
                args.can_change = False
                return

            if isinstance(item, tuple) and len(item) == 2:  # Попадание
                try:
                    low, high = item
                    if low <= new_val <= high:
                        print(f"Изменение свойства '{args.property_name}' на {new_val} запрещено [{low}, {high}]).")
                        args.can_change = False
                        return
                except TypeError:
                    pass


# Базовый класс для моделей с поддержкой событий изменения свойств
class PropertyChangeNotifier:
    '''События изменения свойств'''

    def __init__(self) -> None:
        self.property_changing: Event[PropertyChangingEventArgs] = Event()
        self.property_changed: Event[PropertyChangedEventArgs] = Event()

    def _set_property(self, field_name: str, field_value: Any, new_value: Any) -> bool:
        '''Установки свойства'''
        # Событие до изменения
        changing_args = PropertyChangingEventArgs(field_name, field_value, new_value)
        self.property_changing(self, changing_args)
        if not changing_args.can_change:
            return False
        return True

    def _notify_changed(self, property_name: str) -> None:
        '''Вызов события после изменения'''
        self.property_changed(self, PropertyChangedEventArgs(property_name))


class Person(PropertyChangeNotifier):
    '''человека со свойствами: имя, возраст, email'''

    def __init__(self, name: str, year_of_birth: int, email: str) -> None:
        super().__init__()
        self._name = name
        self._year_of_birth = year_of_birth
        self._email = email

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if self._set_property('name', self._name, value):
            self._name = value
            self._notify_changed('name')

    @property
    def year_of_birth(self) -> int:
        return self._year_of_birth

    @year_of_birth.setter
    def year_of_birth(self, value: int) -> None:
        if self._set_property('year_of_birth', self._year_of_birth, value):
            self._year_of_birth = value
            self._notify_changed('year_of_birth')

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if self._set_property('email', self._email, value):
            self._email = value
            self._notify_changed('email')

    def __repr__(self) -> str:
        return f"Person(name={self._name}, year_of_birth={self._year_of_birth}, email={self._email})"


class Product(PropertyChangeNotifier):
    '''Товар со свойствами: название, цена, количество'''

    def __init__(self, title: str, price: float, quantity: int) -> None:
        super().__init__()
        self._title = title
        self._price = price
        self._quantity = quantity

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if self._set_property('title', self._title, value):
            self._title = value
            self._notify_changed('title')

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if self._set_property('price', self._price, value):
            self._price = value
            self._notify_changed('price')

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if self._set_property('quantity', self._quantity, value):
            self._quantity = value
            self._notify_changed('quantity')

    def __repr__(self) -> str:
        return f"Product(title={self._title}, price={self._price}, quantity={self._quantity})"


def test_events() -> None:
    console_handler = ConsolePropertyChangedHandler()
    year_of_birth_validator = ValidatingPropertyChangingHandler(forbidden_values=[(2000, 2011)])
    price_validator = ValidatingPropertyChangingHandler(forbidden_values=[0.0])

    person = Person("Иван", 1997, "ivan@gooloogooloo.com")
    product = Product("Офисный компьютер", 30000.0, 10)

    person.property_changed += console_handler
    person.property_changing += year_of_birth_validator

    product.property_changed += console_handler
    product.property_changing += price_validator

    print("Изменение свойств Person")
    print(f"До: {person}")
    person.year_of_birth = 1999
    person.year_of_birth = 2007
    person.name = "Дмитрий"
    person.email = "OTCHISLY@gooloogooloo.com"
    print(f"После: {person}")

    print("\nИзменение свойств Product")
    print(f"До: {product}")
    product.price = 90000.0
    product.price = 0.0
    product.quantity = 5
    product.title = "Игровой компьютер (2 ядра 2 гига, игровая видеокарта)"
    print(f"После: {product}")

    print("\nОтписка")
    product.property_changed -= console_handler
    product.quantity = 20
    print("(Изменение quantity произошло, но событие не обработано)")

    print(f"Product после: {product}")


if __name__ == "__main__":
    test_events()

















