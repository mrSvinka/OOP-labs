"""
Лабораторная работа 7 ("внедреж" зависимостей)

Написать сервис, который управляет ассоциациями между интерфейсами и классами их реализующими. См. Dependency Injection (Развитие концециии фабрики классов)

1. Создать класс инжектор, который должен поддерживать
- 3 различных режима жизненного цикла соаздаваемы классов LifeStyle: PerRequest, Scoped, Singleton
- регистрацию зависимости между интерфейсов и классом
 напр: register(self, interface_type, class_type, life_circle)
- возможность передачи дополнительных параметров в конструктор регистрируемого класса
 напр: register(self, interface_type, class_type, life_circle, params)
- использование в конструкторе регистрируемого интерфейса другие уже зарегистрированные интерфейсы
- метод для возвращаения экземпляра класса по интерфейсу.
напр: get_instance(self, interface_type) -> class_instance
- В зависимости от ассоциированного LifeStyle get_instance должен работать по-разному:
    PerRequest => возвращает каждый раз новый экзепляр класса
    Scoped => возвращает один и тот же экземпляр внутри Scope (внутри открытой области). Можно реализовать, например, через with в python
    Singleton => всегда возвращает один и тот же экземпляр объекта
- добавить также возможность ассоциации интерфейса с фабричным методом, возвращающим класс
  напр: register(self, interface_type, fabric_method)

2. Создать  минимум три интерфейса
напр: interface1, interface2, interface3
Под каждый интерфейс создать минимум два класса его поддерживающего с разными LifeCircle
напр: class1_debug(interface1), class1_release(interface1), class2_debug(interface2), class2_release(interface2), class3_debug(interface3), class3_release(interface3)

3. Создать две конфигурации c различными регистрациями реализаций interface1, interface2, interface3

4. Продемонстрировать получение экземпляров классов при помощи инжектора и их дальнейшее использование
"""


import inspect
import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Callable, Type, Union, get_type_hints, List  ############# добавлен импорт List
import contextlib


class LifeStyle(Enum):
    '''Режимы жизненного цикла создаваемых объектов'''
    PER_REQUEST = 1      # каждый раз новый экземпляр
    SCOPED = 2           # один экземпляр в пределах области видимости
    SINGLETON = 3        # один экземпляр на всё время жизни инжектора


########################################################################################################################
class Registration:
    '''Хранит информацию о регистрации интерфейса'''
    def __init__(self,
                 impl: Union[Type, Callable, List[Type]], life_style: LifeStyle, params: Optional[Dict[str, Any]] = None,
                 is_factory: bool = False, is_multiple: bool = False):
        self.impl = impl
        self.life_style = life_style
        self.params = params or {}
        self.is_factory = is_factory
        self.is_multiple = is_multiple
########################################################################################################################


class Injector:
    '''Контейнер внедрения зависимостей'''
    def __init__(self) -> None:
        self._registrations: Dict[Type, Registration] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._scoped_instances: Optional[Dict[Type, Any]] = None

    def register(self, interface: Type, class_type: Union[Type, List[Type]],
                 life_style: LifeStyle = LifeStyle.PER_REQUEST, params: Optional[Dict[str, Any]] = None) -> None:


########################################################################################################################
        if isinstance(class_type, list): #Если передан список
            for cls in class_type:
                if not issubclass(cls, interface):
                    raise TypeError(f"Класс {cls.__name__} не реализует интерфейс {interface.__name__}")
            self._registrations[interface] = Registration(impl=class_type, life_style=life_style, params=params, is_factory=False, is_multiple=True)
        else:
            if not issubclass(class_type, interface): # Обычная регистрация одного класса
                raise TypeError(f"Класс {class_type.__name__} не реализует интерфейс {interface.__name__}")
            self._registrations[interface] = Registration(impl=class_type, life_style=life_style, params=params, is_factory=False, is_multiple=False)
########################################################################################################################


    def register_factory(self, interface: Type, factory: Callable[..., Any],
                         life_style: LifeStyle = LifeStyle.PER_REQUEST) -> None:
        '''Регистрация фабричного метода для интерфейса'''
        self._registrations[interface] = Registration(
            impl=factory, life_style=life_style, is_factory=True)

    @contextlib.contextmanager
    def scope(self):
        '''Контекстный менеджер для работы с областью видимости (Scoped)'''
        if self._scoped_instances is not None:
            raise RuntimeError("Вложенные scope не поддерживаются")
        self._scoped_instances = {}
        try:
            yield
        finally:
            self._scoped_instances = None

    def get_instance(self, interface: Type) -> Any:
        '''Возвращает экземпляр, ассоциированный с интерфейсом, с учётом жизненного цикла'''
        if interface not in self._registrations:
            raise ValueError(f"Интерфейс {interface.__name__} не зарегистрирован")

        reg = self._registrations[interface]

        if reg.life_style == LifeStyle.SINGLETON:
            if interface not in self._singleton_instances:
                #для множественной регистрации класссейчас
                self._singleton_instances[interface] = self._create_instance(reg)
            return self._singleton_instances[interface]

        if reg.life_style == LifeStyle.SCOPED:
            if self._scoped_instances is None:
                raise RuntimeError("Нет активной области видимости (scope)")
            if interface not in self._scoped_instances:
                self._scoped_instances[interface] = self._create_instance(reg)
            return self._scoped_instances[interface]

        return self._create_instance(reg)

    def _create_instance(self, reg: Registration) -> Any:
        '''Создаёт экземпляр согласно регистрации (фабрика или класс)'''
        if reg.is_factory:
            return reg.impl()


########################################################################################################################
        if reg.is_multiple: # обработка множественной регистрации
            chosen_class = random.choice(reg.impl)  # случайно выбираем класс из списка
            return self._create_instance_for_class(chosen_class, reg.params)

        return self._create_instance_for_class(reg.impl, reg.params) # одиночный класс

    def _create_instance_for_class(self, class_type: Type, params: Dict[str, Any]) -> Any: #создание конкретного класса
########################################################################################################################


        # Получаем аннотации типов конструктора
        try:
            type_hints = get_type_hints(class_type.__init__)
        except Exception:
            type_hints = {}

        sig = inspect.signature(class_type.__init__)
        kwargs = {}

        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            #Явно переданные параметры (наивысший приоритет)
            if name in params:
                kwargs[name] = params[name]
                continue
            #Если есть аннотация типа и этот тип зарегистрирован, внедряем зависимость
            if name in type_hints:
                dep_type = type_hints[name]
                if dep_type in self._registrations:
                    kwargs[name] = self.get_instance(dep_type)
                    continue
            #Если у параметра есть значение по умолчанию – пропускаем
            if param.default is not inspect.Parameter.empty:
                continue
            #Обязательный параметр не удалось заполнить
            raise ValueError(f"Не удалось разрешить параметр '{name}' конструктора {class_type.__name__}. "
                f"Зарегистрируйте зависимость типа {type_hints.get(name, '?')} ")

        return class_type(**kwargs)


#Интерфейсы
class ILogger(ABC):
    @abstractmethod
    def log(self, message: str) -> None:
        pass


class IRepository(ABC):
    @abstractmethod
    def get_data(self) -> str:
        pass


class IService(ABC):
    @abstractmethod
    def process(self) -> str:
        pass


#Реализации
class DebugLogger(ILogger):
    def log(self, message: str) -> None:
        print(f"[DEBUG] {message}")


class DebugRepository(IRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_data(self) -> str:
        self.logger.log("DebugRepository.get_data() called")
        return "отладочные данные"


class DebugService(IService):
    def __init__(self, repo: IRepository, logger: ILogger):
        self.repo = repo
        self.logger = logger

    def process(self) -> str:
        self.logger.log("DebugService.process() started")
        data = self.repo.get_data()
        return f"DebugService обработан: {data}"


class ReleaseLogger(ILogger):
    def log(self, message: str) -> None:
        print(f"[RELEASE] {message}")


class ReleaseRepository(IRepository):
    def __init__(self, logger: ILogger, connection_string: str):
        self.logger = logger
        self.connection_string = connection_string

    def get_data(self) -> str:
        self.logger.log(f"ReleaseRepository с использованием {self.connection_string}")
        return "реальные данные о производстве"


class ReleaseService(IService):
    def __init__(self, repo: IRepository):
        self.repo = repo

    def process(self) -> str:
        data = self.repo.get_data()
        return f"ReleaseService обработан: {data}"


########################################################################################################################
#демонстрации множественных регистраций
class ServiceVariantA(IService):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def process(self) -> str:
        self.logger.log("Variant A processing")
        return "Результат варианта A"


class ServiceVariantB(IService):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def process(self) -> str:
        self.logger.log("Variant B processing")
        return "Результат варианта B"


class ServiceVariantC(IService):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def process(self) -> str:
        self.logger.log("Variant C processing")
        return "Результат варианта C"
########################################################################################################################


class AnotherServiceImpl(IService):
    def __init__(self, value: int):
        self.value = value

    def process(self) -> str:
        return f"AnotherService со значением={self.value}"


def another_service_factory() -> IService:
    return AnotherServiceImpl(42)


def configure_debug(inj: Injector) -> None:
    inj.register(ILogger, DebugLogger, LifeStyle.PER_REQUEST)
    inj.register(IRepository, DebugRepository, LifeStyle.PER_REQUEST)
    inj.register(IService, DebugService, LifeStyle.PER_REQUEST)


def configure_release(inj: Injector) -> None:
    inj.register(ILogger, ReleaseLogger, LifeStyle.SINGLETON)
    inj.register(IRepository, ReleaseRepository, LifeStyle.SCOPED,
                 params={"connection_string": "Server=prod;Database=mydb"})
    inj.register(IService, ReleaseService, LifeStyle.PER_REQUEST)


################################################################################
    '''демонстрация множественной регистрации'''
def configure_random(inj: Injector) -> None:
    inj.register(ILogger, DebugLogger, LifeStyle.SINGLETON)
    inj.register(IService,
                 [ServiceVariantA, ServiceVariantB, ServiceVariantC],
                 LifeStyle.PER_REQUEST,
                 params={})
#################################################################################


def demo_debug_configuration():
    print("\n" + "="*50)
    print("Debug конфигурация (все зависимости PerRequest)")
    print("="*50)

    injector = Injector()
    configure_debug(injector)

    srv1 = injector.get_instance(IService)
    srv2 = injector.get_instance(IService)

    print(f"ID сервиса 1: {id(srv1)}")
    print(f"ID сервиса 2: {id(srv2)}")
    print("Результат работы srv1.process():", srv1.process())
    print("Результат работы srv2.process():", srv2.process())


def demo_release_configuration():
    print("\n" + "-"*50)
    print("Release конфигурация")
    print("-"*50)

    injector = Injector()
    configure_release(injector)

    log1 = injector.get_instance(ILogger)
    log2 = injector.get_instance(ILogger)
    print(f"ID логгера 1 (Singleton): {id(log1)}")
    print(f"ID логгера 2 (Singleton): {id(log2)}")

    print("\n--- Внутри первого scope ---")
    with injector.scope():
        repo1 = injector.get_instance(IRepository)
        repo2 = injector.get_instance(IRepository)
        print(f"ID репозитория 1 (Scoped): {id(repo1)}")
        print(f"ID репозитория 2 (Scoped): {id(repo2)}")

        srv1 = injector.get_instance(IService)
        srv2 = injector.get_instance(IService)
        print(f"ID сервиса 1 (PerRequest): {id(srv1)}")
        print(f"ID сервиса 2 (PerRequest): {id(srv2)}")

    print("\n--- Внутри второго scope ---")
    with injector.scope():
        repo3 = injector.get_instance(IRepository)
        print(f"ID репозитория 3: {id(repo3)}")

    print("\n--- Попытка получить Scoped вне scope ---")
    try:
        injector.get_instance(IRepository)
    except RuntimeError as e:
        print(f"Ожидаемая ошибка: {e}")


def demo_factory():
    print("\n" + "-"*50)
    print("Регистрация фабричного метода")
    print("-"*50)

    injector = Injector()
    injector.register_factory(IService, another_service_factory, LifeStyle.SINGLETON)

    srv1 = injector.get_instance(IService)
    srv2 = injector.get_instance(IService)
    print(f"ID фабричного сервиса 1 (Singleton): {id(srv1)}")
    print(f"ID фабричного сервиса 2 (Singleton): {id(srv2)}")
    print("Результат работы:", srv1.process())


##########################################################################################
def demo_random_selection():
    print("\n" + "-"*20 + "Случайный выбор" + "-"*20)

    injector = Injector()
    configure_random(injector)

    results = []
    for i in range(5):
        srv = injector.get_instance(IService)
        results.append((type(srv).__name__, srv.process()))
        print(f"Вызов {i+1}: класс {type(srv).__name__} -> {srv.process()}")
##########################################################################################


def demo_edge_cases():
    print("\n" + "-"*50)
    print("Крайние случаи")
    print("-"*50)

    injector = Injector()

    try:
        injector.get_instance(ILogger)
    except ValueError as e:
        print("Ожидаемая ошибка (нет регистрации):", e)

    class BadService(IService):
        def __init__(self, logger: ILogger):
            self.logger = logger
        def process(self): return ""

    injector.register(IService, BadService, LifeStyle.PER_REQUEST)
    try:
        injector.get_instance(IService)
    except ValueError as e:
        print("Ожидаемая ошибка:", e)


if __name__ == "__main__":
    demo_debug_configuration()
    demo_release_configuration()
    demo_factory()
    demo_random_selection()
    demo_edge_cases()