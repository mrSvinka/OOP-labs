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
from typing import Any, Dict, List, Optional, Type


class OutputManager:
    '''Вывод в консоль и файл'''

    def __init__(self, filename: str = "keyboard_log.txt"):
        self._buffer = []
        self._filename = filename
        open(filename, "w").close()

    def _write(self, text: str):
        print(text)
        with open(self._filename, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def add_char(self, ch: str):
        self._buffer.append(ch)
        self._write("".join(self._buffer))

    def remove_last_char(self):
        if self._buffer:
            self._buffer.pop()
        self._write("".join(self._buffer))

    def print_message(self, msg: str):
        self._write(msg)


class Command(ABC):
    _registry: Dict[str, Type[Command]] = {}

    def __init_subclass__(cls, **kwargs):  # автоматическая регистрация
        """Автоматическая регистрация подкласса по имени класса."""
        super().__init_subclass__(**kwargs)
        type_name = getattr(cls, 'command_type', cls.__name__)
        Command._registry[type_name] = cls

    @classmethod
    def get_class(cls, type_name: str) -> Optional[Type[Command]]:  # получить класс по имени
        return cls._registry.get(type_name)

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:  # превратить в словарь
        """Возвращает словарь для сериализации команды"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any], out: OutputManager) -> Command:  # создать из словаря
        """Создаёт команду из словаря."""
        pass

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class PrintCharCommand(Command):
    command_type = "PrintChar"

    def __init__(self, char: str, out: OutputManager):
        self.char = char
        self.out = out

    def to_dict(self) -> Dict[str, Any]:  # превратить в словарь
        return {"type": self.command_type, "char": self.char}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], out: OutputManager) -> PrintCharCommand:  # создать из словаря
        return cls(data["char"], out)

    def execute(self):
        self.out.add_char(self.char)

    def undo(self):
        self.out.remove_last_char()


class VolumeUpCommand(Command):
    command_type = "VolumeUp"

    def __init__(self, out: OutputManager):
        self.out = out

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.command_type}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], out: OutputManager) -> VolumeUpCommand:
        return cls(out)

    def execute(self):
        self.out.print_message("Volume increased +20%")

    def undo(self):
        self.out.print_message("Volume decreased -20%")


class VolumeDownCommand(Command):
    command_type = "VolumeDown"

    def __init__(self, out: OutputManager):
        self.out = out

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.command_type}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], out: OutputManager) -> VolumeDownCommand:
        return cls(out)

    def execute(self):
        self.out.print_message("Volume decreased -20%")

    def undo(self):
        self.out.print_message("Volume increased +20%")


class MediaPlayerCommand(Command):
    command_type = "MediaPlayer"

    def __init__(self, out: OutputManager):
        self.out = out

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.command_type}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], out: OutputManager) -> MediaPlayerCommand:
        return cls(out)

    def execute(self):
        self.out.print_message("Media player launched")

    def undo(self):
        self.out.print_message("Media player closed")


class EchoCommand(Command):
    command_type = "Echo"

    def __init__(self, message: str, out: OutputManager):
        self.message = message
        self.out = out

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.command_type, "message": self.message}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], out: OutputManager) -> EchoCommand:
        return cls(data["message"], out)

    def execute(self):
        self.out.print_message(self.message)

    def undo(self):
        self.out.print_message(f"Undo: {self.message}")


class Keyboard:
    def __init__(self, out: OutputManager):
        self._out = out
        self._bindings = {}
        self._history = []
        self._redo = []

    def bind(self, key: str, cmd: Command):
        self._bindings[key] = cmd

    def press(self, key: str):
        if key not in self._bindings:
            self._out.print_message(f"<{key} не связан>")
            return
        cmd = self._bindings[key]
        cmd.execute()
        self._history.append(cmd)
        self._redo.clear()

    def undo(self):
        if not self._history:
            self._out.print_message("<ничего нельзя отменить>")
            return
        cmd = self._history.pop()
        cmd.undo()
        self._redo.append(cmd)

    def redo(self):
        if not self._redo:
            self._out.print_message("<ничего переделывать не нужно>")
            return
        cmd = self._redo.pop()
        cmd.execute()
        self._history.append(cmd)

    def get_snapshot(self):
        snap = {}
        for key, cmd in self._bindings.items():
            snap[key] = cmd.to_dict()
        return snap

    def restore_snapshot(self, snap: dict):
        self._bindings.clear()
        for key, desc in snap.items():
            cmd_type = desc.get("type")
            cmd_class = Command.get_class(cmd_type)
            if cmd_class:
                cmd = cmd_class.from_dict(desc, self._out)
                self._bindings[key] = cmd


class KeyboardMemento:
    def __init__(self, bindings_snapshot: Dict[str, Dict[str, Any]]):
        self._bindings = bindings_snapshot

    def get_bindings(self) -> Dict[str, Dict[str, Any]]:
        return self._bindings.copy()


class KeyboardStateEncoder:
    def __init__(self, rename_map: Optional[Dict[str, str]] = None,
                 exclude: Optional[List[str]] = None):
        self.rename_map = rename_map or {}
        self.exclude = exclude or []

    def encode(self, keyboard: Keyboard) -> Dict[str, Any]:
        raw_bindings = keyboard.get_snapshot()
        data = {"bindings": raw_bindings}

        for field in self.exclude:
            data.pop(field, None)

        for old, new in self.rename_map.items():
            if old in data:
                data[new] = data.pop(old)

        return data

    def decode(self, data: Dict[str, Any], output: OutputManager) -> KeyboardMemento:
        reverse_rename = {v: k for k, v in self.rename_map.items()}
        for new, old in reverse_rename.items():
            if new in data:
                data[old] = data.pop(new)

        bindings = data.get("bindings", {})
        return KeyboardMemento(bindings)


class KeyboardStateSaver:
    def __init__(self, encoder: KeyboardStateEncoder, filename: str = "keyboard_state.json"):
        self.encoder = encoder
        self.filename = filename

    def save(self, keyboard: Keyboard) -> None:
        data = self.encoder.encode(keyboard)
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, keyboard: Keyboard) -> bool:
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

    kb.bind("x", EchoCommand("новое", out))
    kb.bind("y", EchoCommand("очень новое", out))

    out.print_message("\n---------------Демонстрация----------------")
    for key in ["a", "b", "c", "x", "y", "undo", "undo", "redo", "ctrl++", "ctrl+-", "ctrl+p", "d", "undo", "undo"]:
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