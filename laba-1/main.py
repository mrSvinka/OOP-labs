'''
Предмет: Объектно ориентированное программирование. Лабораторная работа 1

Создать класс Angle для хранения углов !
 - хранить внутреннее состоние угла в радианах !
 - возможность создания угла в радианах и градусах  !
 - реализовать присваивание и получение угла в раддианах и градусах !
 - релизовать перобразование угла в строку, float, int, str !
  - реализовать строкове представление объекта (str, repr) !
 - реализовать сложение (в том числе с float и int, считая, что они заданы в радианах), вычитание (считая, что они заданы в радианах), умножение и деление на число !
- реализовать сранение углов с учетом, что 2 Pi*N + x = x, где Pi=3.14.1529..., N-целое !
 - реализовать сравнение углов !

 Создать класс AngleRange для хранения промежтка для углов
 - Реализовать механизм создания объекта через задание начальной и конечной точки промежукта в виде углов float, int или Angle
 - Предусмотреть возможность использования включающих и исключающих промежутков
 - реализовать возможность сравнения объектов на эквивалентность (eq)
 - реализовать строкове представление объекта (str, repr)
 - реализовать получение длины промежутка (abs или отдельны метод)
 - реализовать сравнение промежутков
 - реализовать операцию in для проверки входит один промежуток в другой или угол в промежуток
 - реализовать операции сложения, вычитания  (результат в общем виде - список промежутков)
'''


import math

class Angle:
    _TWOPI = 2 * math.pi  # константа для 2π

    def __init__(self, value=0, radians=True):  # инициализация класса
        if radians:
            self._radians = float(value)
        else:
            self._radians = math.radians(float(value))  # градусы в радианы

    # Свойства для удобного доступа
    @property
    def radians(self):
        '''Значение угла в радианах'''
        return self._radians

    @property
    def degrees(self):
        '''Значение угла в градусах'''
        return math.degrees(self._radians)

    # Методы получения значений
    def get_radians(self):
        '''Значение угла в радианах'''
        return self._radians

    def get_degrees(self):
        '''Значение угла в градусах'''
        return math.degrees(self._radians)

    # Методы установки значений
    def set_radians(self, value):
        '''Значение угла в радианах'''
        self._radians = float(value)

    def set_degrees(self, value):
        '''Значение угла в градусах'''
        self._radians = math.radians(float(value))  # Конвертируем градусы в радианы и сохраняем

    # нормализация угла
    def _normalized(self):
        '''Возвращает нормализованное значение угла в диапазоне [0, 2π)'''
        rad = self._radians % self._TWOPI
        # Учитываем отрицательные углы
        if rad < 0:
            rad += self._TWOPI
        return rad

    # Методы преобразования типов
    def __float__(self):
        '''Преобразование во float'''
        return self._radians

    def __int__(self):
        '''Преобразование в int '''
        return int(self._radians)

    def __str__(self):
        '''Преобразование в строку'''
        return f"Angle({self._radians:.4f} rad, {self.get_degrees():.2f}°)"

    def __repr__(self):
        return f"Angle({self._radians})"

    # Арифметические операции
    def __add__(self, other):
        '''Сложение углов'''
        if isinstance(other, (int, float)):
            return Angle(self._radians + other)  # Сложение с числом (в радианах)
        elif isinstance(other, Angle):
            return Angle(self._radians + other._radians)  # Сложение с другим углом
        return NotImplemented

    def __radd__(self, other):
        '''Правостороннее сложение'''
        return self.__add__(other)

    def __sub__(self, other):
        '''Вычитание'''
        if isinstance(other, (int, float)):
            return Angle(self._radians - other)
        elif isinstance(other, Angle):
            return Angle(self._radians - other._radians)
        return NotImplemented

    def __rsub__(self, other):
        '''Правостороннее вычитание'''
        if isinstance(other, (int, float)):
            return Angle(other - self._radians)
        return NotImplemented

    def __mul__(self, other):
        '''Умножение'''
        if isinstance(other, (int, float)):
            return Angle(self._radians * other)
        return NotImplemented

    def __rmul__(self, other):
        '''Правостороннее умножение'''
        return self.__mul__(other)

    def __truediv__(self, other):
        '''Деление на число'''
        if isinstance(other, (int, float)):
            return Angle(self._radians / other)
        return NotImplemented

    def __rtruediv__(self, other):
        '''Правостороннее деление'''
        if isinstance(other, (int, float)):
            return Angle(other / self._radians)
        return NotImplemented

    # Методы сравнения (с учетом периодичности)
    def __eq__(self, other):
        '''Проверка на равенство'''
        if isinstance(other, Angle):
            return math.isclose(self._normalized(), other._normalized())  # Сравниваем нормализованные углы
        return False

    def __ne__(self, other):
        '''Проверка на неравенство'''
        return not self.__eq__(other)

    def __lt__(self, other):
        '''Меньше'''
        if isinstance(other, Angle):
            return self._normalized() < other._normalized()
        return NotImplemented

    def __le__(self, other):
        '''Меньше или равно'''
        if isinstance(other, Angle):
            return self._normalized() <= other._normalized()
        return NotImplemented

    def __gt__(self, other):
        '''Больше'''
        if isinstance(other, Angle):
            return self._normalized() > other._normalized()
        return NotImplemented

    def __ge__(self, other):
        '''Больше или равно'''
        if isinstance(other, Angle):
            return self._normalized() >= other._normalized()
        return NotImplemented


class AngleRange:
    def __init__(self, start, end, start_included=True, end_included=False):
        self.start = self._to_angle(start)
        self.end = self._to_angle(end)
        self.start_included = bool(start_included)
        self.end_included = bool(end_included)

        # Нормализованные значения
        self._norm_start = self.start._normalized()
        self._norm_end = self.end._normalized()

        # Определяем, пересекает ли диапазон 0
        if self._norm_start <= self._norm_end:
            self._cont_start, self._cont_end = self._norm_start, self._norm_end
            self._crosses_zero = False
        else:
            self._cont_start, self._cont_end = self._norm_start, self._norm_end + Angle._TWOPI
            self._crosses_zero = True

    @staticmethod
    def _to_angle(value):
        if isinstance(value, Angle):
            return Angle(value.get_radians())  # Используем метод get_radians() вместо атрибута radians
        elif isinstance(value, (int, float)):
            return Angle(value)
        raise TypeError(f"Неподдерживаемый тип: {type(value)}")

    def __abs__(self):
        length = self._cont_end - self._cont_start
        if not self.start_included:
            length -= 1e-12
        if not self.end_included:
            length -= 1e-12
        return max(0, length)

    length = property(__abs__)

    def __str__(self):
        s, e = ('[', ']') if self.start_included else ('(', ')')
        return f"AngleRange{s}{self.start.get_degrees():.1f}°, {self.end.get_degrees():.1f}°{e}"  # Исправлено: get_degrees()

    def __repr__(self):
        s, e = ('[', ']') if self.start_included else ('(', ')')
        return f"AngleRange{s}{self.start._radians:.4f} rad, {self.end._radians:.4f} rad{e}"

    def __eq__(self, other):
        if not isinstance(other, AngleRange):
            return False

        return (math.isclose(self._norm_start, other._norm_start) and
                math.isclose(self._norm_end, other._norm_end) and
                self.start_included == other.start_included and
                self.end_included == other.end_included)

    def __contains__(self, item):
        # Проверка вхождения угла
        if isinstance(item, (Angle, int, float)):
            angle = self._to_angle(item)
            angle_norm = angle._normalized()

            if not self._crosses_zero:
                if self._norm_start < angle_norm < self._norm_end:
                    return True
                if math.isclose(angle_norm, self._norm_start):
                    return self.start_included
                if math.isclose(angle_norm, self._norm_end):
                    return self.end_included
                return False
            else:
                if self._norm_start < angle_norm < Angle._TWOPI:
                    return True
                if 0 <= angle_norm < self._norm_end:
                    return True
                if math.isclose(angle_norm, self._norm_start):
                    return self.start_included
                if math.isclose(angle_norm, self._norm_end):
                    return self.end_included
                return False

        # Проверка вхождения диапазона
        if isinstance(item, AngleRange):
            # Простая проверка: все границы текущего диапазона должны содержаться в другом
            return (self.start in item and self.end in item)

        return NotImplemented

    # Сравнение диапазонов
    def __lt__(self, other):
        return isinstance(other, AngleRange) and self._cont_start < other._cont_start

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not (self <= other)

    def __ge__(self, other):
        return not (self < other)

    # Операции с диапазонами (упрощенные)
    def __add__(self, other):
        if not isinstance(other, AngleRange):
            return NotImplemented

        # Если диапазоны пересекаются или соприкасаются, объединяем
        if self._intersects(other):
            # Определяем новые границы
            starts = [(self._cont_start, self.start_included),
                      (other._cont_start, other.start_included)]
            ends = [(self._cont_end, self.end_included),
                    (other._cont_end, other.end_included)]

            new_start = min(starts, key=lambda x: x[0])
            new_end = max(ends, key=lambda x: x[0])

            return [AngleRange(
                Angle(new_start[0] % Angle._TWOPI),
                Angle(new_end[0] % Angle._TWOPI),
                new_start[1], new_end[1]
            )]

        return [self, other]

    def __sub__(self, other):
        if not isinstance(other, AngleRange):
            return NotImplemented

        if not self._intersects(other):
            return [self]

        # Упрощенная реализация: возвращаем левую и правую части
        result = []

        # Левая часть
        if self._cont_start < other._cont_start:
            left_end = min(self._cont_end, other._cont_start)
            if left_end - self._cont_start > 1e-12:
                result.append(AngleRange(
                    Angle(self._cont_start), Angle(left_end),
                    self.start_included, not other.start_included
                ))

        # Правая часть
        if self._cont_end > other._cont_end:
            right_start = max(self._cont_start, other._cont_end)
            if self._cont_end - right_start > 1e-12:
                result.append(AngleRange(
                    Angle(right_start), Angle(self._cont_end),
                    not other.end_included, self.end_included
                ))

        return result

    def _intersects(self, other):
        '''Проверяет пересечение двух диапазонов'''
        if not isinstance(other, AngleRange):
            return False

        # Разбиваем на непрерывные части
        self_parts = self._split()
        other_parts = other._split()

        for sp in self_parts:
            for op in other_parts:
                if self._ranges_intersect(sp, op):
                    return True
        return False

    def _split(self):
        '''Разбивает диапазон на непрерывные части'''
        if not self._crosses_zero:
            return [self]
        return [
            AngleRange(self.start, Angle(Angle._TWOPI), self.start_included, False),
            AngleRange(Angle(0), self.end, True, self.end_included)
        ]

    @staticmethod
    def _ranges_intersect(r1, r2):
        '''Проверяет пересечение двух непрерывных диапазонов'''
        # Проверяем перекрытие
        if r1._cont_end < r2._cont_start or r2._cont_end < r1._cont_start:
            return False

        # Проверяем касание
        if math.isclose(r1._cont_end, r2._cont_start):
            return r1.end_included and r2.start_included
        if math.isclose(r2._cont_end, r1._cont_start):
            return r2.end_included and r1.start_included

        return True


def test_angle():
    print("Тестирование класса Angle")

    # Создание углов
    a1 = Angle(math.pi)  # 180 градусов
    a2 = Angle(90, radians=False)  # 90 градусов
    a3 = Angle(45, radians=False)

    print(f"a1 = {a1}")
    print(f"a2 = {a2}")
    print(f"a3 = {a3}")

    # Проверка get/set методов
    print(f"\n--- Get/Set методы ---")
    print(f"a1 в градусах: {a1.get_degrees():.2f}°")
    print(f"a2 в радианах: {a2.get_radians():.4f}")

    a1.set_degrees(270)
    print(f"a1 после set_degrees(270): {a1}")
    a1.set_radians(math.pi / 2)
    print(f"a1 после set_radians(pi/2): {a1}")

    # Арифметические операции
    print(f"\n--- Арифметические операции ---")
    sum_angle = a2 + a3
    print(f"a2 + a3 = {sum_angle}")
    print(f"a2 * 2 = {a2 * 2}")
    print(f"a2 / 2 = {a2 / 2}")
    print(f"a2 - a3 = {a2 - a3}")
    print(f"a2 + 1.0 = {a2 + 1.0}")

    # Сравнение углов
    print(f"\n--- Сравнение углов ---")
    print(f"a2 == a3? {a2 == a3}")
    print(f"a2 > a3? {a2 > a3}")
    print(f"a2 < a3? {a2 < a3}")

    # Преобразование типов
    print(f"\n--- Преобразование типов ---")
    print(f"float(a2) = {float(a2):.4f}")
    print(f"int(a2) = {int(a2)}")
    print(f"str(a2) = {str(a2)}")
    print(f"repr(a2) = {repr(a2)}")


def test_angle_range():
    print("\n\nТестирование класса AngleRange")

    # Создание диапазонов
    r1 = AngleRange(0, 90, start_included=True, end_included=True)  # 0-90° включительно
    r2 = AngleRange(Angle(45, radians=False), Angle(135, radians=False))  # 45-135°, начало включено, конец исключен
    r3 = AngleRange(270, 45)  # Диапазон через 0

    print(f"r1 = {r1}")
    print(f"r2 = {r2}")
    print(f"r3 = {r3}")

    # Длина диапазона
    print(f"\n--- Длина диапазонов ---")
    print(f"Длина r1: {abs(r1):.4f} рад ({r1.length:.4f} рад)")
    print(f"Длина r2: {abs(r2):.4f} рад")
    print(f"Длина r3: {abs(r3):.4f} рад")

    # Проверка вхождения угла
    print(f"\n--- Проверка вхождения углов ---")
    test_angles = [Angle(0, radians=False), Angle(45, radians=False),
                   Angle(90, radians=False), Angle(135, radians=False)]
    for angle in test_angles:
        print(f"{angle.get_degrees():.1f}° в r1? {angle in r1}")
        print(f"{angle.get_degrees():.1f}° в r2? {angle in r2}")

    # Проверка вхождения диапазона
    print(f"\n--- Проверка вхождения диапазонов ---")
    small_range = AngleRange(20, 40)
    print(f"[20°,40°] в r1? {small_range in r1}")

    # Сравнение диапазонов
    print(f"\n--- Сравнение диапазонов ---")
    print(f"r1 == r2? {r1 == r2}")

    # Операции с диапазонами
    print(f"\n--- Операции с диапазонами ---")

    # Пересекающиеся диапазоны
    r4 = AngleRange(60, 120)
    union_result = r1 + r4
    print(f"r1 + [60°,120°] = {union_result}")

    # Непересекающиеся диапазоны
    r5 = AngleRange(150, 180)
    union_result2 = r1 + r5
    print(f"r1 + [150°,180°] = {union_result2}")

    # Вычитание
    diff_result = r2 - AngleRange(70, 100)
    print(f"r2 - [70°,100°] = {diff_result}")


def test_edge_cases():
    print("\n\n=== Крайние случаи ===")

    # Углы больше 2π
    large_angle = Angle(3 * math.pi)
    print(f"Угол 3π = {large_angle}")

    # Отрицательные углы
    neg_angle = Angle(-math.pi / 2)
    print(f"Угол -π/2 = {neg_angle}")

    # Диапазон с отрицательными значениями
    r_neg = AngleRange(-45, 45)
    print(f"Диапазон [-45°,45°] = {r_neg}")
    print(f"Длина: {abs(r_neg):.4f} рад")

    # Точечный диапазон
    point_range = AngleRange(30, 30, start_included=True, end_included=True)
    print(f"Точечный диапазон [30°,30°] = {point_range}")
    print(f"Длина: {abs(point_range):.4f} рад")


if __name__ == "__main__":
    print("Тестирование классов Angle и AngleRange")
    print("=" * 50)

    test_angle()
    test_angle_range()
    test_edge_cases()

    print("\n" + "=" * 50)
    print("Тестирование завершено")