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
from typing import Any, Dict, List, Optional


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


class Command:
    def execute(self): raise NotImplementedError
    def undo(self): raise NotImplementedError


class PrintCharCommand(Command):
    def __init__(self, char: str, out: OutputManager):
        self.char = char
        self.out = out

    def execute(self): self.out.add_char(self.char)
    def undo(self): self.out.remove_last_char()


class VolumeUpCommand(Command):
    def __init__(self, out: OutputManager): self.out = out
    def execute(self): self.out.print_message("Volume increased +20%")
    def undo(self): self.out.print_message("Volume decreased -20%")


class VolumeDownCommand(Command):
    def __init__(self, out: OutputManager): self.out = out
    def execute(self): self.out.print_message("Volume decreased -20%")
    def undo(self): self.out.print_message("Volume increased +20%")


class MediaPlayerCommand(Command):
    def __init__(self, out: OutputManager): self.out = out
    def execute(self): self.out.print_message("Media player launched")
    def undo(self): self.out.print_message("Media player closed")


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
                continue
            self._bindings[key] = cmd


class KeyboardStateSaver:
    def __init__(self, filename="keyboard_state.json", rename=None):
        self.filename = filename
        self.rename = rename or {}

    def save(self, keyboard: Keyboard):
        snap = keyboard.get_snapshot()
        if self.rename: # переименование ключей
            data = {"keymap": snap}  # сразу нужное имя
        else:
            data = {"bindings": snap}
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, keyboard: Keyboard) -> bool:
        if not os.path.exists(self.filename):
            return False
        with open(self.filename) as f:
            data = json.load(f)
        if self.rename:
            snap = data.get("keymap", {})
        else:
            snap = data.get("bindings", {})
        keyboard.restore_snapshot(snap)
        return True


def main():
    out = OutputManager()
    kb = Keyboard(out)

    # Загружаем, если есть
    saver = KeyboardStateSaver(rename={"bindings": "keymap"})
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






