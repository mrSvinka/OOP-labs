'''
Лабораторная работа 2 (красивая консоль)

Создать класс для вывода текста в консоль в произвольном месте, произвольным цветом, большим псевдошрифтом.
Вывод цветом осуществляется при помощи управляющих ANSI команд, использовать внешние библиотеки запрещено.
Управляющие команды не расставлять в виде текста по всему коду, а сохранить в виде констант или перечислителей.
Вывод псевдошрифтом осуществляется путем задания в текстовом файле (формат на ваше усмотрение, json,, xml, ...) шаблонов символов
(достаточно задать шаблоны только букв одного алфавита).
Например,
   *     ****
 *  *     *
 ****     *
*    *    *

Класс должен уметь:
1) выводить статически (python: classmethod) текст в произвольном месте, произвольным цветом (цвет задавать при помощи типа данных перечислитель Enum) произвольным символом
Например:
Printer.print(text: str, color: Color, position : Tuple[int, int], symbol: str)
2) создавать экземпляр с фиксированным цветом и позицией для дальнейшего вывода текста в едином стиле с поддержкой возвращения состояния косноли в исходное состояние
    (поддержка в Python: with, в C#: using, в С++: используйте деструктор)
Например:
with Printer(color: Color, position : Tuple[int, int], symbol: str) as printer:
       printer.print('text1')
       printer.print('text2')
3) использовать произвольный символ для вывода псевдотекста (в примере шаблонов используется символ *)

Продемонстрировать
1. работу класса как статическим образом, так и с использованием создания экземпляра класса, используя with (using и.т.п.).
2. независимость работы класса от поданного файла с шаблонами букв, реализовав шрифты высотой 5 и 7 символов
'''



import json
import os
from enum import Enum
from typing import Dict, List, Tuple



counting = 1
indent = 4


class Color(Enum):
    '''Цвета (ANSI-коды)'''
    RED = 31
    GREEN = 32
    MAGENTA = 35
    WHITE = 37
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    YELLOW = 33


class ANSI:
    '''Константы и вспом. методы для ANSI-escape'''
    RESET = "\033[0m"      # Сброс всех атрибутов (цвет, фони т.д.)
    SAVE_CURSOR = "\033[s"  # Сохранить текущую позицию курсора
    RESTORE_CURSOR = "\033[u" # Восстановить сохранённую позицию курсора

    @staticmethod
    def set_color(color: Color) -> str:
        '''Возвращает послед. уст. цвета'''
        return f"\033[{color.value}m"

    @staticmethod
    def set_position(row: int, col: int) -> str:
        '''Возвращает послед. перемещения курсора'''
        return f"\033[{row};{col}H"



class FontLoader:
    '''Загрузчик шрифтов из файлов'''

    @staticmethod
    def load_font(filename: str) -> Dict[str, List[str]]:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                font_data = json.load(f)

            if not isinstance(font_data, dict):
                raise ValueError("Неверный формат шрифта")

            heights = {len(pattern) for pattern in font_data.values()}
            if len(heights) > 1:
                raise ValueError(f"Несовместимые высоты символов: {heights}")

            return font_data

        except Exception as e:
            print(f"Ошибка загрузки шрифта {filename}: {e}")
            return {}



class Printer:
    '''Класс для вывода текста'''

    def __init__(self, color: Color = Color.WHITE, position: Tuple[int, int] = (1, 1),
                 symbol: str = "*", font_file: str | None = None):
        self.color = color          #цвет текста
        self.position = position    #начальная позиция
        self.symbol = symbol        #символ, которым заполняется псевдографика
        self._font: Dict[str, List[str]] = {}
        self._font_height: int = 0
        self._original_position: Tuple[int, int] | None = None

        if font_file:
            self.load_font(font_file)

    def load_font(self, font_file: str) -> None:
        '''Загружает шрифт из файла'''
        self._font = FontLoader.load_font(font_file)
        if self._font:
            first_char = next(iter(self._font.values()))
            self._font_height = len(first_char)

    def __enter__(self) -> "Printer":
        '''Сохраняет текущую позицию курсора'''
        print(ANSI.SAVE_CURSOR, end="")
        self._original_position = self.position
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        '''Восстанавливает курсор и сбрасывает цвет )при выходе из блока)'''
        print(ANSI.RESET + ANSI.RESTORE_CURSOR, end="")

    @classmethod
    def print(cls, text: str, color: Color = Color.WHITE,
              position: Tuple[int, int] = (1, 1), symbol: str = "*",
              font_file: str | None = None) -> None:
        '''Статический метод для однократного вывода текста'''
        font: Dict[str, List[str]] = {}
        font_height = 0

        if font_file: # Попытка загрузить шрифт
            font = FontLoader.load_font(font_file)
            if font:
                first_char = next(iter(font.values()))
                font_height = len(first_char)

        if not font:  #Шрифт не загружен — обычный текст
            print(ANSI.set_position(*position) + ANSI.set_color(color) +
                  text + ANSI.RESET)
            return

        lines = [""] * font_height  #Подготовка строк псевдографики

        for char in text.upper(): # Обработка каждого символа входного текста
            if char == " ":
                for i in range(font_height):
                    lines[i] += " " * indent
                continue

            if char in font:
                pattern = font[char]
                for i, pat_line in enumerate(pattern):
                    rendered = pat_line.replace("*", symbol) #Заменяем * на заданный символ
                    lines[i] += rendered + " "
            else:  #Если символа нет в шрифте, пропускаем
                for i in range(font_height):
                    lines[i] += " " * (font_height + counting )

        start_row, start_col = position  #Вывод по строкам
        for i, line in enumerate(lines):
            print(ANSI.set_position(start_row + i, start_col) +
                  ANSI.set_color(color) + line + ANSI.RESET, end="")

    def print_text(self, text: str, position: Tuple[int, int] | None = None) -> None:
        '''Вывод текста с использованием настроек экземпляра'''
        if not self._font:
            print("Ошибка, шрифт не загружен")
            return
        
        pos = position if position is not None else self.position

        lines = [""] * self._font_height

        for char in text.upper():
            if char == " ":
                for i in range(self._font_height):
                    lines[i] += " " * indent
                continue

            if char in self._font: 
                pattern = self._font[char]
                for i, pat_line in enumerate(pattern):
                    rendered = pat_line.replace("*", self.symbol)
                    lines[i] += rendered + " "
            else:
                for i in range(self._font_height):
                    lines[i] += " " * (self._font_height + counting )

        start_row, start_col = pos
        for i, line in enumerate(lines):
            print(ANSI.set_position(start_row + i, start_col) +
                  ANSI.set_color(self.color) + line + ANSI.RESET, end="")

        if position is None:
            self.position = (start_row + self._font_height + counting , start_col)


def demonstrate() -> None:
    '''Демонстрация работы Printer'''
    os.system("cls" if os.name == "nt" else "clear")

    print("Демонстрация работы PRINTER\n")

    # 1.Статический вывод со шрифтом 5x5
    Printer.print("HELLO", Color.YELLOW, (3, 5), "@", "font5x5.json")
    Printer.print("WORLD", Color.GREEN, (9, 5), "#", "font5x5.json")
    input(" ")

    # 2.Контекстный менеджер (5x5)
    with Printer(Color.MAGENTA, (15, 5), "$", "font5x5.json") as p:
        p.print_text("HELLO")
        p.print_text("WORLD")
    input(" ")

    # 3.Статический вывод (7x7)
    Printer.print("HELLO", Color.BRIGHT_YELLOW, (27, 5), "%", "font7x7.json")
    Printer.print("WORLD", Color.BRIGHT_CYAN, (35, 5), "^", "font7x7.json")
    input(" ")

    # 4.Контекстный менеджер (7x7)
    with Printer(Color.RED, (43, 5), "#", "font7x7.json") as p:
        p.print_text("HELLO")
    input(" ")


    print(ANSI.set_position(55, 1))

if __name__ == "__main__":
    demonstrate()