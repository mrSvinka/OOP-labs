'''

@abc.abstractmethod - это декоратор из модуля abc (Abstract Base Classes), который помечает метод как абстрактный.
Это означает, что класс, содержащий такой метод, становится абстрактным и не может быть инстанциирован напрямую. Подклассы обязаны переопределить этот метод.

match - это метод, который проверяет, подходит ли сообщение под условие фильтра.

format - это метод, который преобразует исходное сообщение в строку с дополнительной информацией .

АТРИБУТ


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



BUFFER_MAX = 777

# ТИПЫ
class LogLevel(enum.Enum):
    '''Уровни логирования'''
    INFO = 'INFO'
    WARN = 'WARN'
    ERROR = 'ERROR'


class ILogFilter(abc.ABC):
    '''Интерфейс фильтра логов'''

    @abc.abstractmethod
    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Проходит ли сообщение через фильтр'''
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


# ФИЛЬТРЫ
class SimpleLogFilter(ILogFilter):
    '''Фильтр по вхождению подстроки в текст'''

    def __init__(self, pattern: str) -> None:
        self._pattern = pattern

    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Возвращает True, если паттерн содержится в тексте'''
        return self._pattern in text


###################################################################ЗДЕСЯ ИЗМЕНЕНИЕ##################################################################
class ReLogFilter(ILogFilter):
    '''Фильтр по регулярному выражению'''

    def __init__(self, pattern: str) -> None:
        self._regex = None
        try:
            self._regex = re.compile(pattern)
        except re.error:
            pass

    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Регулярное выражение найдено в тексте'''
        if self._regex is None:
            return False
        try:
            return bool(self._regex.search(text))
        except Exception:
            return False
#################################################################################################################################################################

class LevelFilter(ILogFilter):
    '''Фильтр по уровню логирования'''

    def __init__(self, *levels: LogLevel) -> None:
        self._levels = set(levels)

    def match(self, log_level: LogLevel, text: str) -> bool:
        '''Уровень сообщения присутствует в наборе'''
        return log_level in self._levels


################################################################ЕЩЕ МЕНЯЛ##############################################################################
class OrderedHandler(ILogHandler):
    '''Сообщения в порядке: ERROR, WARN, INFO'''

    def __init__(self, target_handler: ILogHandler, max_size: int = 100) -> None:

        self._target = target_handler  # переданы отсортированные сообщения
        self._buffer = []  # список кортежей (priority, log_level, text)
        self._max_size = max_size

        self._priority_map = {
            LogLevel.ERROR: 0,
            LogLevel.WARN: 1,
            LogLevel.INFO: 2
        }

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Добавляет сообщение в буфер с приоритетом'''

        self._buffer.append((self._priority_map[log_level], log_level, text))
        if len(self._buffer) >= self._max_size:
            self.flush()

    def flush(self) -> None:
        '''Сортирует буфер по приоритету, передаёт всё обработчику'''
        self._buffer.sort(key=lambda x: x[0])  # сортировка по приоритету
        for _, level, msg in self._buffer:
            self._target.handle(level, msg)
        self._buffer.clear()  # очистка буфера


########################################################################################################################################################################

# ОБРАБОТЧИКИ
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
    '''Отправка через UDP-сокет'''

    def __init__(self, host: str = '127.0.0.1', port: int = 514) -> None:
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Создаём UDP-сокет

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Отправляет сообщение как UDP-дейтаграмму'''
        try:
            self._socket.sendto(text.encode('utf-8'), (self._host, self._port))
        except Exception:
            pass

    def __del__(self):
        '''При удалении объекта, закрывает сокет'''
        self._socket.close()


class SyslogHandler(ILogHandler):
    '''отправка логов в формате syslog'''

    def __init__(self, host: str = '127.0.0.1', port: int = 514) -> None:
        self._handler = SocketHandler(host, port)  # используем тот же UDP

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Форматирует сообщение в стиле syslog и отправляет'''
        # Уровни важности
        priority_map = {
            LogLevel.INFO: 14,  # user.info
            LogLevel.WARN: 12,  # user.warn
            LogLevel.ERROR: 11  # user.err
        }
        pri = priority_map[log_level]
        syslog_msg = f"<{pri}>1 {text}"
        self._handler.handle(log_level, syslog_msg)


class FtpHandler(ILogHandler):
    '''Отправка логов на FTP-сервер'''

    def __init__(self, host: str, username: str, password: str, remote_path: str) -> None:
        self._host = host
        self._username = username
        self._password = password
        self._remote_path = remote_path

    def handle(self, log_level: LogLevel, text: str) -> None:
        '''Устанавливает FTP-соединение, дописывает сообщение'''
        try:
            import ftplib
            with ftplib.FTP(self._host) as ftp:  # Создаём временный файл с сообщением
                ftp.login(self._username, self._password)
                with open('temp_log.txt', 'w') as tmp:  # Подключаемся к FTP
                    tmp.write(text + '\n')
                with open('temp_log.txt', 'rb') as f:  # Открываем временный файл и передаём его в удалённый
                    ftp.storbinary(f'APPE {self._remote_path}', f)
                os.remove('temp_log.txt')  # Удаляем временный файл
        except Exception:
            pass


# ФОРМАТТЕРЫ
##################################################################ТУТА ИЗМЕНЕНИЕ####################################################################
class DefaultFormatter(ILogFormatter):
    '''Уровень, дата и время, текст'''

    def __init__(self, date_format: str = "%Y.%m.%d %H:%M:%S") -> None:  # по умолчанию
        self._date_format = date_format

    def format(self, log_level: LogLevel, text: str) -> str:
        '''Возвращает строку вида [<LEVEL>] [<YYYY.MM.DD HH:MM:SS>] <text>'''
        now = datetime.datetime.now()
        timestamp = now.strftime(self._date_format)
        return f"[{log_level.value}] [{timestamp}] {text}"


#################################################################################################################################################################

# JCYJDYJQ RKFCC
class Logger:
    '''Получает списки фильтров, форматтеров и обработчиков'''

    def __init__(self,
                 filters: Optional[List[ILogFilter]] = None,
                 formatters: Optional[List[ILogFormatter]] = None,
                 handlers: Optional[List[ILogHandler]] = None) -> None:
        self._filters = filters if filters is not None else []
        self._formatters = formatters if formatters is not None else []
        self._handlers = handlers if handlers is not None else []

    def log(self, log_level: LogLevel, text: str) -> None:
        '''Пропускает сообщение через фильтры, форматтеры. отправляет обработчикам'''
        # Фильтрация
        for f in self._filters:
            if not f.match(log_level, text):
                return

                # Форматирование
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


def demo_logger():
    print("1.Запись в консоль и файл:")
    logger_basic = Logger(
        formatters=[DefaultFormatter()],
        handlers=[ConsoleHandler(), FileHandler('demo.log')]
    )
    logger_basic.log_info("Информация")
    logger_basic.log_warn("Предупреждение")
    logger_basic.log_error("Ошибкаааааааа")
    print("   → Проверьте файл demo.log\n")

    print("2. Фильтрация по уровню (только ERROR/WARN):")
    logger_level = Logger(
        filters=[LevelFilter(LogLevel.ERROR, LogLevel.WARN)],
        formatters=[DefaultFormatter()],
        handlers=[ConsoleHandler()]
    )
    logger_level.log_info("INFO не выводится")
    logger_level.log_warn("WARN выводится")
    logger_level.log_error("ERROR выводится")
    print()

    print("3. Фильтрация по подстроке:")
    logger_simple = Logger(
        filters=[SimpleLogFilter("важно")],
        formatters=[DefaultFormatter()],
        handlers=[ConsoleHandler()]
    )
    logger_simple.log_info("обычное сообщение")
    logger_simple.log_info("важное сообщение")
    print()

    print("4.Фильтрация по регулярному выражению:")
    logger_regex = Logger(
        filters=[ReLogFilter(r"\d{3}")],
        #filters=[ReLogFilter(r"\\///[.\\dsahedthterashated648nds452..d{3}")],
        formatters=[DefaultFormatter()],
        handlers=[ConsoleHandler()]
    )
    logger_regex.log_info("код 777")
    logger_regex.log_info("код 123")
    logger_regex.log_error("ошибка 228")
    print()

    print("5. Несколько обработчиков (консоль, файл, UDP-сокет):")
    logger_multi = Logger(
        formatters=[DefaultFormatter()],
        handlers=[
            ConsoleHandler(),
            FileHandler('multi_demo.log'),
            SocketHandler('127.0.0.1', 9999)
        ]
    )
    logger_multi.log_info("Сообщение")
    print("   → Проверьте файл multi_demo.log и UDP-порт 9999\n")

    print("7.ERROR, WARN, INFO")
    ordered_handler = OrderedHandler(ConsoleHandler(), max_size=BUFFER_MAX)
    logger_ordered = Logger(
        formatters=[DefaultFormatter()],
        handlers=[ordered_handler]
    )
    logger_ordered.log_error("Ошибкааа")
    logger_ordered.log_info("Информация")
    logger_ordered.log_warn("Предупреждение")
    logger_ordered.log_info("Информулина")
    logger_ordered.log_error("Ошибкаааааа")
    logger_ordered.log_info("Информейшен")


    ordered_handler.flush()
    print()

    print("8.нестандартным форматом дат")
    logger_timeonly = Logger(
        formatters=[DefaultFormatter(date_format="%H:%M:%S")],
        handlers=[ConsoleHandler()]
    )
    logger_timeonly.log_info("Только время")
    print()

    Logger().log_info("Нет обработчиков → ничего не выведется")
    Logger(handlers=[ConsoleHandler()]).log_info("Только обработчик")
    print()


if __name__ == "__main__":
    demo_logger()