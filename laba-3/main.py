'''
Лабораторная работа 3 (Система логирования)

Создать систему логирования, применяя композицию (агрегацию),
с возможностью фильтрации и различных способов вывода информации.
Использовать либо протоколы, либо интерфейсы, либо чисто абстрактные классы в зависимости от используемого языка программирования.

1. Создать перечислитель LogLevel со значениями INFO, WARN, ERROR
 - LevelFilter - для фильтрации на основе перечислителя (его также создать )

2. Создать протокол/интерфейс фильтров ILogFilter / LogFilterProtocol:
  - match(self, log_level: LogLevel, text: str) -> bool

3. Создать несколько классов реализующих данный протокол/интерфейс
 - SimpleLogFilter - для фильтрации по вхождению паттерна, задаваемого текстом, в текст сообщения
 - ReLogFilter - для фильтрации по вхождению паттерна, задаваемого регулярным выражением, в текст сообщения
 - LevelFilter - Для фильтрации по LogLevel

4. Создать протокол/интерфейс обработчиков ILogHandler / LogHandlerProtocol:
 - handle(self, log_level: LogLevel, text: str) -> None

5. Создать неcколько классов реализующих данный протокол/интерфейс
 - FileHandler - для записи логов в файл
 - SocketHandler - для отправки логов через сокет
 - ConsoleHandler - для вывода логово в консоль
 - SyslogHandler - для записи логов в системные логи
 - FtpHandler - для записи логов на ftp сервер

6. Создать протокол/интерфейс обработчиков ILogFormatter / LogFormatterProtocol:
 - format(self, log_level: LogLevel, text: str) -> str

7. Реализовать форматтер, который к каждому сообщению в логах добавляет данные по следующему формату:
[<log_level>] [<data:yyyy.MM.dd hh:mm:ss>] <text>
где <>  - плейсхолдеры, которые должны быть заменены на значения переменных

8. Реализовать класс Logger, который принимает
  - список ILogFilter / LogFilterProtocol
  - список  ILogFormatter / LogFormatterProtocol
  - список ILogHandler / LogHandlerProtocol

 и реализует:
 - log(self, log_level: LogLevel, text: str) -> None - которая прогоняет логи через фильтры, потом последовательно через все форматтеры и отдает обработчикам
 - log_info(text: str) -> None - записывает логи с LogLevel = LogLevel.INFO
 - log_warn(text: str) -> None - записывает логи с LogLevel = LogLevel.WARN
 - log_error(text: str) -> None - записывает логи с LogLevel = LogLevel.ERROR


9. Продемонстрировать работу спроектированной системы классов
'''

from __future__ import annotations
import abc
import enum
import re
import socket
import datetime
import sys
import os
from typing import List, Optional, Union


class LogLevel(enum.Enum):
    '''Перечислитель уровней логирования'''
    INFO = 'INFO'
    WARN = 'WARN'
    ERROR = 'ERROR'


class ILogFilter(abc.ABC):
    '''Интерфейс фильтра логов'''

    @abc.abstractmethod
    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Проверяет, проходит ли сообщение через фильтр'''
        pass


class ILogHandler(abc.ABC):
    '''Интерфейс обработчика логов'''

    @abc.abstractmethod
    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Обрабатывает отформатированное сообщение'''
        pass


class ILogFormatter(abc.ABC):
    '''Интерфейс форматтера логов'''

    @abc.abstractmethod
    def format(self, log_level: LogLevel, text: str) -> str:
        '''Форматирует сообщение'''
        pass


class SimpleLogFilter(ILogFilter):
    '''Фильтр по вхождению подстроки (паттерна) в текст сообщения'''

    def __init__(self, pattern: str) -> None:
        self._pattern = pattern

    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Возвращает True, если паттерн содержится в тексте'''
        return self._pattern in text


class ReLogFilter(ILogFilter):
    '''Фильтр по регулярному выражению'''

    def __init__(self, pattern: str) -> None:
        self._regex = re.compile(pattern)

    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Возвращает True, если регулярное выражение найдено в тексте'''
        return bool(self._regex.search(text))


class LevelFilter(ILogFilter):
    '''Фильтр по уровню логирования'''

    def __init__(self, *levels: LogLevel) -> None:
        self._levels = set(levels)

    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Возвращает True, если уровень сообщения присутствует в наборе'''
        return log_level in self._levels


class ConsoleHandler(ILogHandler):
    '''Вывод логов в консоль (stdout)'''

    def __init__(self, stream=None) -> None:
        self._stream = stream or sys.stdout

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Печатает сообщение в консоль'''
        print(text, file=self._stream)


class FileHandler(ILogHandler):
    '''Запись логов в файл'''

    def __init__(self, filename: str, mode: str = 'a', encoding: str = 'utf-8') -> None:
        self._filename = filename
        self._mode = mode
        self._encoding = encoding

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Дописывает сообщение в файл'''
        with open(self._filename, self._mode, encoding=self._encoding) as f:
            f.write(text + '\n')


class SocketHandler(ILogHandler):
    '''Отправка логов через UDP-сокет'''

    def __init__(self, host: str = '127.0.0.1', port: int = 514) -> None:
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Отправляет сообщение как UDP-дейтаграмму'''
        try:
            self._socket.sendto(text.encode('utf-8'), (self._host, self._port))
        except Exception as e:
            # В реальном коде можно логировать ошибку, но здесь просто игнорируем
            pass

    def __del__(self):
        '''Закрываем сокет при удалении объекта'''
        self._socket.close()


class SyslogHandler(ILogHandler):
    '''Отправка логов в системный syslog.Через UDP на localhost:514 (стандартный порт syslog)'''

    def __init__(self, host: str = '127.0.0.1', port: int = 514) -> None:
        self._handler = SocketHandler(host, port)  # используем тот же UDP

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Форматирует сообщение в стиле syslog и отправляет'''
        # Примитивный syslog-формат: < PRI > version ...
        # Уровни важности: INFO=6, WARN=4, ERROR=3 (user-level)
        priority_map = {
            LogLevel.INFO: 14,    # user.info
            LogLevel.WARN: 12,     # user.warn
            LogLevel.ERROR: 11     # user.err
        }
        pri = priority_map[log_level]
        syslog_msg = f"<{pri}>1 {text}"
        self._handler.handle(log_level, syslog_msg)


class FtpHandler(ILogHandler):
    '''Отправка логов на FTP-сервер (упрощённо, запись в файл на сервере)'''

    def __init__(self, host: str, username: str, password: str, remote_path: str) -> None:
        self._host = host
        self._username = username
        self._password = password
        self._remote_path = remote_path

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Устанавливает FTP-соединение и дописывает сообщение в удалённый файл. Для упрощения используем ftplib, но в демо можно заменить заглушкой'''
        try:
            import ftplib
            with ftplib.FTP(self._host) as ftp:
                ftp.login(self._username, self._password)
                # Предполагаем, что remote_path указывает на файл, в который можно писать
                # Используем команду APPE для добавления
                with open('temp_log.txt', 'w') as tmp:
                    tmp.write(text + '\n')
                with open('temp_log.txt', 'rb') as f:
                    ftp.storbinary(f'APPE {self._remote_path}', f)
                os.remove('temp_log.txt')
        except Exception as e:
            # В реальном проекте нужно логировать ошибки
            pass


class DefaultFormatter(ILogFormatter):
    '''Форматтер, добавляющий уровень и временную метку'''

    def format(self, log_level: LogLevel, text: str) -> str:
        '''Возвращает строку вида [INFO] [2025.02.17 14:35:22] сообщение'''
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y.%m.%d %H:%M:%S")
        return f"[{log_level.value}] [{timestamp}] {text}"


class Logger:
    '''Основной класс логгера. Принимает списки фильтров, форматтеров и обработчиков'''

    def __init__(self,
                 filters: Optional[List[ILogFilter]] = None,
                 formatters: Optional[List[ILogFormatter]] = None,
                 handlers: Optional[List[ILogHandler]] = None) -> None:
        self._filters = filters if filters is not None else []
        self._formatters = formatters if formatters is not None else []
        self._handlers = handlers if handlers is not None else []

    def log(self, log_level: LogLevel, text: str) -> None:
        '''Пропускает сообщение через фильтры, форматтеры и отправляет обработчикам. Если фильтры не пусты, все они должны вернуть True'''
        # Фильтрация
        for f in self._filters:
            if not f.match(log_level, text):
                return  # сообщение отброшено

        # Форматирование (последовательное применение)
        formatted_text = text
        for fmt in self._formatters:
            formatted_text = fmt.format(log_level, formatted_text)

        # Отправка обработчикам
        for h in self._handlers:
            h.handle(log_level, formatted_text)

    def log_info(self, text: str) -> None:
        '''Логирование с уровнем INFO'''
        self.log(LogLevel.INFO, text)

    def log_warn(self, text: str) -> None:
        '''Логирование с уровнем WARN'''
        self.log(LogLevel.WARN, text)

    def log_error(self, text: str) -> None:
        '''Логирование с уровнем ERROR'''
        self.log(LogLevel.ERROR, text)


def test_logger_basic():
    print("Тестирование базового функционала Logger")

    # Создаём обработчики
    console = ConsoleHandler()
    file_handler = FileHandler('test.log')

    # Форматтер
    formatter = DefaultFormatter()

    # Логгер с одним форматтером и двумя обработчиками
    logger = Logger(
        formatters=[formatter],
        handlers=[console, file_handler]
    )

    print("Запись сообщений:")
    logger.log_info("Это информационное сообщение")
    logger.log_warn("Предупреждение")
    logger.log_error("Ошибка")

    print("Проверьте файл test.log\n")


def test_filters():
    print("Тестирование фильтров")

    console = ConsoleHandler()
    formatter = DefaultFormatter()

    # Фильтры
    level_filter = LevelFilter(LogLevel.ERROR, LogLevel.WARN)          # только ERROR и WARN
    simple_filter = SimpleLogFilter("важно")                           # сообщения со словом "важно"
    regex_filter = ReLogFilter(r"\d{3}")                               # сообщения, содержащие трёхзначное число

    logger1 = Logger(
        filters=[level_filter],
        formatters=[formatter],
        handlers=[console]
    )
    logger2 = Logger(
        filters=[simple_filter],
        formatters=[formatter],
        handlers=[console]
    )
    logger3 = Logger(
        filters=[regex_filter],
        formatters=[formatter],
        handlers=[console]
    )

    print("Логгер с фильтром по уровню (только ERROR/WARN):")
    logger1.log_info("info сообщение")        # не должно вывестись
    logger1.log_warn("warn сообщение")        # выведется
    logger1.log_error("error сообщение")      # выведется

    print("\nЛоггер с фильтром по подстроке 'важно':")
    logger2.log_info("обычное сообщение")
    logger2.log_info("важное сообщение")

    print("\nЛоггер с regex-фильтром (трёхзначное число):")
    logger3.log_info("код 42")
    logger3.log_info("код 123")
    logger3.log_error("ошибка 500")


def test_handlers():
    print("Тестирование различных обработчиков (заглушки)")

    # Для демонстрации используем только консоль, т.к. другие требуют внешних ресурсов
    console = ConsoleHandler()
    # SocketHandler попытается отправить UDP на localhost:514 (можно проверить netcat)
    socket_handler = SocketHandler('127.0.0.1', 9999)  # нестандартный порт, чтобы не мешать syslog
    # FileHandler
    file_handler = FileHandler('multi_test.log')
    # SyslogHandler использует SocketHandler
    syslog_handler = SyslogHandler('127.0.0.1', 9999)
    # FtpHandler - заглушка (попытается соединиться, но если нет сервера, просто выбросит исключение)
    # Чтобы не замедлять тест, закомментируем или сделаем try
    # ftp_handler = FtpHandler('localhost', 'user', 'pass', '/log.txt')

    formatter = DefaultFormatter()

    logger = Logger(
        formatters=[formatter],
        handlers=[console, socket_handler, file_handler, syslog_handler]
    )

    logger.log_info("Тест множественных обработчиков")
    print("Проверьте файл multi_test.log, а также UDP-порт 9999 (если слушает netcat)")


def test_edge_cases_logger():
    print("Крайние случаи: пустые списки, отсутствие фильтров и т.д.")

    # Логгер без фильтров, форматтеров и обработчиков (ничего не произойдёт)
    logger_empty = Logger()
    logger_empty.log_info("Это сообщение никуда не попадёт")

    # Логгер только с обработчиком
    console = ConsoleHandler()
    logger_min = Logger(handlers=[console])
    logger_min.log_info("Сообщение без форматирования")  # выведется как есть

    # Логгер с форматтером, но без обработчиков
    formatter = DefaultFormatter()
    logger_no_handlers = Logger(formatters=[formatter])
    logger_no_handlers.log_info("Это сообщение будет отформатировано, но не выведено")


if __name__ == "__main__":
    test_logger_basic()
    test_filters()
    test_handlers()
    test_edge_cases_logger()
    print("Тестирование системы логирования завершено")