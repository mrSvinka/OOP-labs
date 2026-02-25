'''
Лабораторная работа 6 (виртуальная клавиатура)

Создать класс виртуальной клавиутуры, которая поддерживает:
- добавление/изменение ассоциации клавиши/комбинации клавиш с командой, которую она выполняет
- откат последней выполненной команды (операция undo)
- возврат последней выполненной команды после выполнения отката (операция redo)
- сохренения добавленных ассоциаций на жесткий диск и восстановление при перезапуске программы

Реализовать класс, используя паттерн Command. При этом реализовать комманды:
- команда, которая печатает символ (сделать класс, который обрабатывает все символы, а не много классов под каждый символ), при этом в случае отмены действия стирает последний выведенный символ
(можно реализовать курс вправо, напечать пробел, курсор вправо)
- команда, которая симулирует увеличение звука (реальную работу со звуком делать не нужно, а просто выводить информацию в текстовом режиме)
- команда, которая симулирует уменьшение звука (реальную работу со звуком делать не нужно, а просто выводить информацию в текстовом режиме)
- команда, которая симулирует запуск медиа плеера (реальную работу с плеером делать не нужно, а просто выводить информацию в текстовом режиме)
- можно добавить что-то свое

Сделать сохранение состояния клавиатуры, используя модифицированный паттерн Memento (то есть за сохранение/восстановление ассоциаций должен отвечать отдельный класс, а не класс клавиатуры).
При этом реализовать и использовать общую схему для сериализации по примеру разобранному на практике:
- не заависит от формата (но для примера реализации рекомендую использовать формат json (но можно и xml, bson, yaml, и даже для нестандартно мыслящих личностей csv или xslx))
- поддерживает тонкую натройку процесса сериализации (переименование полей, пропуск части полей)
- механизм сериализации и десираилизации в отдельногм классе
- механизм представления класса в виде словря также в отдельном классе

Вывод работы программы сделать либо в консоль либо в текстовый файл в подобном  виде (это приер, его повторять необязательно):
CONSOLE:                                                    TEXT FILE:
a                                                                    a
b                                                                    ab
c                                                                    abc
undo                                                                 ab
undo                                                                 a
redo                                                                 ab
ctrl++                                                               volume increased +20%
ctrl+-                                                               volume decreased +20%
ctrl+p                                                               media player launched
d                                                                    abd
undo                                                                 ab
undo                                                                 media player closed

Работу приложение выводить в текстовый файл и в консоль

То есть у вас будет примерно  следующий набор классов:
Keyboard, KeyCommand, VolumeUpCommand, VolumeDownCommand, MediaPlayerCommand, KeybordStateSaver

Создавать графический интерфейс необходимости нет, но если кто-то хочет, я ничего против не имею...
Обратите внимание, что стирание истории != откат действия назад
Обратите внимание, что классы команд не должны зависеть от класса виртуальной клавиатуры
'''



from __future__ import annotations
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class OutputManager:
    '''Вывод в консоль и файл'''
    def __init__(self, filename: str = "keyboard_log.txt"):
        self._buffer = []   # список символов текущей строки
        self._filename = filename
        open(filename, "w").close()

    def _write(self, text: str):    # печатает в консоль и файл
        print(text)
        with open(self._filename, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def add_char(self, ch: str):
        self._buffer.append(ch)
        self._write("".join(self._buffer))

    def remove_last_char(self):     # удалить последний символ из буфера
        if self._buffer:
            self._buffer.pop()
        self._write("".join(self._buffer))

    def print_message(self, msg: str):  # сообщение
        self._write(msg)


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class PrintCharCommand(Command):
    def __init__(self, char: str, out: OutputManager):
        self.char = char
        self.out = out

    def execute(self):
        self.out.add_char(self.char)

    def undo(self):
        self.out.remove_last_char()


class VolumeUpCommand(Command):
    def __init__(self, out: OutputManager):
        self.out = out

    def execute(self):
        self.out.print_message("Volume increased +20%")

    def undo(self):
        self.out.print_message("Volume decreased -20%")


class VolumeDownCommand(Command):
    def __init__(self, out: OutputManager):
        self.out = out

    def execute(self):
        self.out.print_message("Volume decreased -20%")

    def undo(self):
        self.out.print_message("Volume increased +20%")


class MediaPlayerCommand(Command):
    def __init__(self, out: OutputManager):
        self.out = out

    def execute(self):
        self.out.print_message("Media player launched")

    def undo(self):
        self.out.print_message("Media player closed")


class Keyboard:
    def __init__(self, out: OutputManager):
        self._out = out      # менеджер вывода
        self._bindings = {}  # словарь
        self._history = []   # стек выполненных команд
        self._redo = []      # стек отменённых команд

    def bind(self, key: str, cmd: Command):     # привязать команду к клавише
        self._bindings[key] = cmd

    def press(self, key: str):
        if key not in self._bindings:
            self._out.print_message(f"<{key} не связан>")
            return
        cmd = self._bindings[key]  # получить команду
        cmd.execute()              # выполнить
        self._history.append(cmd)  # добавить в историю
        self._redo.clear()         # очистка

    def undo(self):
        if not self._history:
            self._out.print_message("<ничего нельзя отменить>")
            return
        cmd = self._history.pop()  # взять последнюю команду
        cmd.undo()                 # отменить
        self._redo.append(cmd)

    def redo(self):
        if not self._redo:
            self._out.print_message("<ничего переделывать не нужно>")
            return
        cmd = self._redo.pop()
        cmd.execute()               # выполнить сново
        self._history.append(cmd)   # добавить обратно

    def get_snapshot(self):
        snap = {}
        for key, cmd in self._bindings.items():
            if isinstance(cmd, PrintCharCommand):
                snap[key] = {"type": "PrintChar", "char": cmd.char}
            elif isinstance(cmd, VolumeUpCommand):
                snap[key] = {"type": "VolumeUp"}
            elif isinstance(cmd, VolumeDownCommand):
                snap[key] = {"type": "VolumeDown"}
            elif isinstance(cmd, MediaPlayerCommand):
                snap[key] = {"type": "MediaPlayer"}
        return snap

    def restore_snapshot(self, snap: dict):
        self._bindings.clear()
        for key, desc in snap.items():
            t = desc.get("type")
            if t == "PrintChar":
                cmd = PrintCharCommand(desc["char"], self._out)
            elif t == "VolumeUp":
                cmd = VolumeUpCommand(self._out)
            elif t == "VolumeDown":
                cmd = VolumeDownCommand(self._out)
            elif t == "MediaPlayer":
                cmd = MediaPlayerCommand(self._out)
            else:
                continue # неизвестный тип пропускаем
            self._bindings[key] = cmd


class KeyboardMemento:
    def __init__(self, bindings_snapshot: Dict[str, Dict[str, Any]]):
        self._bindings = bindings_snapshot

    def get_bindings(self) -> Dict[str, Dict[str, Any]]:
        return self._bindings.copy()


class KeyboardStateEncoder:
    def __init__(self, rename_map: Optional[Dict[str, str]] = None,
                 exclude: Optional[List[str]] = None):
        self.rename_map = rename_map or {}  # словарь для переименования полей
        self.exclude = exclude or []        # список полей для исключения

    def encode(self, keyboard: Keyboard) -> Dict[str, Any]:
        '''Возвращает словарь для сериализации'''
        raw_bindings = keyboard.get_snapshot()
        data = {"bindings": raw_bindings}

        # Применяем исключение полей
        for field in self.exclude:
            data.pop(field, None)

        # Применяем переименование полей
        for old, new in self.rename_map.items():
            if old in data:
                data[new] = data.pop(old)

        return data

    def decode(self, data: Dict[str, Any], output: OutputManager) -> KeyboardMemento:
        """Восстанавливает из словаря, применяя обратные преобразования"""
        reverse_rename = {v: k for k, v in self.rename_map.items()}
        for new, old in reverse_rename.items():
            if new in data:
                data[old] = data.pop(new)

        # Исключённые поля уже отсутствуют
        bindings = data.get("bindings", {})
        return KeyboardMemento(bindings)


class KeyboardStateSaver:
    '''Отвечает в JSON'''
    def __init__(self, encoder: KeyboardStateEncoder, filename: str = "keyboard_state.json"):
        self.encoder = encoder
        self.filename = filename

    def save(self, keyboard: Keyboard) -> None:
        '''Сохраняет клавиатуры в файл'''
        data = self.encoder.encode(keyboard)
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, keyboard: Keyboard) -> bool:
        '''Загружает состояние из файла и восстанавливает привязки'''
        if not os.path.exists(self.filename):
            return False
        with open(self.filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        memento = self.encoder.decode(data, keyboard._out)
        keyboard.restore_snapshot(memento.get_bindings())
        return True


def main():
    out = OutputManager()
    kb = Keyboard(out)

    encoder = KeyboardStateEncoder(rename_map={"bindings": "keymap"})
    saver = KeyboardStateSaver(encoder, "keyboard_state.json")

    if saver.load(kb):
        out.print_message("----------------Загружено------------------")
    else:
        out.print_message("----------Привязки по умолчанию------------")
        kb.bind("a", PrintCharCommand("a", out))
        kb.bind("b", PrintCharCommand("b", out))
        kb.bind("c", PrintCharCommand("c", out))
        kb.bind("d", PrintCharCommand("d", out))
        kb.bind("ctrl++", VolumeUpCommand(out))
        kb.bind("ctrl+-", VolumeDownCommand(out))
        kb.bind("ctrl+p", MediaPlayerCommand(out))

    out.print_message("\n---------------Демонстрация----------------")
    for key in ["a", "b", "c", "undo", "undo", "redo", "ctrl++", "ctrl+-", "ctrl+p", "d", "undo", "undo"]:
        if key == "undo":
            kb.undo()
        elif key == "redo":
            kb.redo()
        else:
            kb.press(key)

    saver.save(kb)
    out.print_message("\n-------Текущие привязки сохранены---------")


if __name__ == "__main__":
    main()