'''
Лабораторная работа 5 (система авторизации)

Создать систему авторизации и хранения информации о пользователях приложении, не зависящую от
источника данных, поддерживающую автоматическую авторизацию пользователей, реализующую взаимодействие с источником данных
обобщенным образом.

Реализуем через паттерн репозиторий

1. Создать класс User с атрибутами:
    id: int
    name: str
    login: str
    password: str (поле не должно показываться при строковом представлении класс)
    email: str (сделать поле необязательным)
    address: str (сделать поле необязательным)

- Сделать, чтобы коллекция классов User умела сортироваться по полю name.
- Реализовать через dataclass или через аналоги в других языках (C# и Java: record)

2. Создать интерфейс / протокол IDataRepository[T] / DataRepsitoryProtocol[T] для системы CRUD = Create, Read, Update, Delete для произвольного типа данных:
  - get_all(self) -> Sequence[T]
  - get_by_id(self, id: int) -> T | None
  - add(self, item: T) -> None
  - update(self, item: T) -> None
  - delete(self, item: T) -> None

2. Создать интерфейс / протокол IUserRepository ( IDataRepository[User]) / UserRepositoryProtocol (DataRepsitoryProtocol[User]) для взаимодействия с типом данных User
 - get_by_login(self, login: str) -> User | None

3. Создать реализацию  DataRepository[T](IDataRepository[T) / DataRepitoryProtocol[T] supports IDataRepsitoryProtocol[T]
  - Осуществляет хранение данных в файле
  - Можно использовать сторонние сериализаторы (Напр., pickle, json, xml)

4. Создать реализацию UserRepository(IUserRepository) / supports UserRepositoryProtocol на основе DataRepository[T](IDataRepository[T) / DataRepitoryProtocol[T]

5. Создать интерфейс / протокол IAuthService / AuthServiceProtocol
  - sign_in(self, user: User) -> None
  - sign_out(selg, user: User) -> None
  - is_authorized -> bool
  - current_user  -> User

6. Создать реализацию IAuthService / AuthServiceProtocol, которая хранит информацию о текущем пользователе в файле и автоматически авторизует пользователя при повторном заходе в программу в случае наличия соответствующей записи в файле

7. Продемонстрировать работу реализованной системы
 - добавление пользователя
 - редактирование свойств пользователя
 - авторизация пользователя
 - смена текущего пользователя
 - авторматическая авторизация при повторном заходе в программу
'''

"""
Лабораторная работа 5 (система авторизации)

Создать систему авторизации и хранения информации о пользователях приложении, не зависящую от
источника данных, поддерживающую автоматическую авторизацию пользователей, реализующую взаимодействие с источником данных
обобщенным образом.

Реализуем через паттерн репозиторий

1. Создать класс User с атрибутами:
    id: int
    name: str
    login: str
    password: str (поле не должно показываться при строковом представлении класс)
    email: str (сделать поле необязательным)
    address: str (сделать поле необязательным)

- Сделать, чтобы коллекция классов User умела сортироваться по полю name.
- Реализовать через dataclass или через аналоги в других языках (C# и Java: record)

2. Создать интерфейс / протокол IDataRepository[T] / DataRepsitoryProtocol[T] для системы CRUD = Create, Read, Update, Delete для произвольного типа данных:
  - get_all(self) -> Sequence[T]
  - get_by_id(self, id: int) -> T | None
  - add(self, item: T) -> None
  - update(self, item: T) -> None
  - delete(self, item: T) -> None

2. Создать интерфейс / протокол IUserRepository ( IDataRepository[User]) / UserRepositoryProtocol (DataRepsitoryProtocol[User]) для взаимодействия с типом данных User
 - get_by_login(self, login: str) -> User | None

3. Создать реализацию  DataRepository[T](IDataRepository[T) / DataRepitoryProtocol[T] supports IDataRepsitoryProtocol[T]
  - Осуществляет хранение данных в файле
  - Можно использовать сторонние сериализаторы (Напр., pickle, json, xml)

4. Создать реализацию UserRepository(IUserRepository) / supports UserRepositoryProtocol на основе DataRepository[T](IDataRepository[T) / DataRepitoryProtocol[T]

5. Создать интерфейс / протокол IAuthService / AuthServiceProtocol
  - sign_in(self, user: User) -> None
  - sign_out(selg, user: User) -> None
  - is_authorized -> bool
  - current_user  -> User

6. Создать реализацию IAuthService / AuthServiceProtocol, которая хранит информацию о текущем пользователе в файле и автоматически авторизует пользователя при повторном заходе в программу в случае наличия соответствующей записи в файле

7. Продемонстрировать работу реализованной системы
 - добавление пользователя
 - редактирование свойств пользователя
 - авторизация пользователя
 - смена текущего пользователя
 - авторматическая авторизация при повторном заходе в программу
"""

import os
import pickle
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Sequence, List, TypeVar, Generic


# Хеширование паролей
def hash_password(password: str) -> str:
    '''Возвращает строку вида 'salt$hash' для безопасного хранения'''
    salt = os.urandom(16).hex()
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(plain_password: str, hashed: str) -> bool:
    '''Соответствует ли открытый пароль сохранённому хешу'''
    try:
        salt, hash_value = hashed.split("$")
    except ValueError:
        return False
    check_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
    return check_hash == hash_value


@dataclass
class User:
    '''Модель пользователя'''
    id: int
    name: str
    login: str
    password: str = field(repr=False)  # содержит salt$hash
    email: Optional[str] = None
    address: Optional[str] = None

    def __lt__(self, other: 'User') -> bool:
        '''Для сортировки по имени'''
        return self.name < other.name


T = TypeVar('T')  #Интерфейсы репозиториев

class IDataRepository(ABC, Generic[T]):
    @abstractmethod
    def get_all(self) -> Sequence[T]: ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]: ...

    @abstractmethod
    def add(self, item: T) -> None: ...

    @abstractmethod
    def update(self, item: T) -> None: ...

    @abstractmethod
    def delete(self, item: T) -> None: ...


class IUserRepository(IDataRepository[User], ABC):
    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]: ...


class DataRepository(IDataRepository[T], Generic[T]):
    '''Хранение'''
    def __init__(self, filename: str):
        self._filename = filename
        self._items: List[T] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._filename):
            try:
                with open(self._filename, "rb") as f:
                    self._items = pickle.load(f)
            except Exception:
                self._items = []

    def _save(self) -> None:
        with open(self._filename, "wb") as f:
            pickle.dump(self._items, f)

    def get_all(self) -> Sequence[T]:
        return self._items.copy()

    def get_by_id(self, id: int) -> Optional[T]:
        for item in self._items:
            if getattr(item, "id", None) == id:
                return item
        return None

    def add(self, item: T) -> None:
        if hasattr(item, "id") and item.id is not None and self.get_by_id(item.id):
            raise ValueError(f"Элемент с id {item.id} уже имеется")
        self._items.append(item)
        self._save()

    def update(self, item: T) -> None:
        for i, existing in enumerate(self._items):
            if hasattr(existing, "id") and hasattr(item, "id") and existing.id == item.id:
                self._items[i] = item
                self._save()
                return
        raise ValueError("Элемент не найден")

    def delete(self, item: T) -> None:
        self._items = [i for i in self._items if getattr(i, "id", None) != getattr(item, "id", None)]
        self._save()


class UserRepository(IUserRepository):
    def __init__(self, filename: str = "users.pkl"):
        self._repo = DataRepository[User](filename)

    def get_all(self) -> Sequence[User]:
        return self._repo.get_all()

    def get_by_id(self, id: int) -> Optional[User]:
        return self._repo.get_by_id(id)

    def add(self, user: User) -> None:
        # Хеширует пароль перед сохранением если он ещё не в формате salt$hash
        if user.password and "$" not in user.password:
            user.password = hash_password(user.password)
        if user.id is None:
            max_id = max((u.id for u in self._repo.get_all()), default=0)
            user.id = max_id + 1
        self._repo.add(user)

    def update(self, user: User) -> None:
        # Если передан открытый пароль, хешируем
        if user.password and "$" not in user.password:
            user.password = hash_password(user.password)
        self._repo.update(user)

    def delete(self, user: User) -> None:
        self._repo.delete(user)

    def get_by_login(self, login: str) -> Optional[User]:
        for u in self._repo.get_all():
            if u.login == login:
                return u
        return None


# Интерфейс сервиса авторизации
class IAuthService(ABC):
    @abstractmethod
    def sign_in(self, user: User) -> None: ...

    @abstractmethod
    def sign_out(self, user: User) -> None: ...

    @abstractmethod
    def is_authorized(self) -> bool: ...

    @abstractmethod
    def current_user(self) -> Optional[User]: ...


class AuthService(IAuthService):
    '''Авторизация через файл сессии'''
    SESSION_FILE = "session.pkl"

    def __init__(self, user_repository: IUserRepository):
        self._user_repo = user_repository
        self._current_user: Optional[User] = None
        self._load_session()

    def _load_session(self) -> None:
        if os.path.exists(self.SESSION_FILE):
            try:
                with open(self.SESSION_FILE, "rb") as f:
                    user_id = pickle.load(f)
                    self._current_user = self._user_repo.get_by_id(user_id)
            except Exception:
                pass

    def _save_session(self) -> None:
        if self._current_user:
            with open(self.SESSION_FILE, "wb") as f:
                pickle.dump(self._current_user.id, f)
        else:
            try:
                os.remove(self.SESSION_FILE)
            except FileNotFoundError:
                pass

    def sign_in(self, user: User) -> None:
        stored = self._user_repo.get_by_login(user.login)
        if stored and verify_password(user.password, stored.password):
            self._current_user = stored
            self._save_session()

    def sign_out(self, user: User) -> None:
        if self._current_user and self._current_user.id == user.id:
            self._current_user = None
            self._save_session()

    def is_authorized(self) -> bool:
        return self._current_user is not None

    def current_user(self) -> Optional[User]:
        return self._current_user


def demonstrate() -> None:
    '''Удаляем предыдущие файлы'''
    for f in ("users.pkl", "session.pkl"):
        if os.path.exists(f):
            os.remove(f)

    print("-------------------СИСТЕМА АВТОРИЗАЦИИ------------------\n")

    repo = UserRepository()
    auth = AuthService(repo)

    '''Добавление пользователей'''
    u1 = User(id=None, name="Алеся", login="login", password="password", email="email@gmail.com")
    u2 = User(id=None, name="Не бей", login="ZACHOT", password="228611", address="ул. Невского, 14")
    repo.add(u1)
    repo.add(u2)

    print("\nСортировка пользователей по имени:")
    for u in sorted(repo.get_all()):
        print(f"{u.id}: {u.name} ({u.login})")

    print("\nРедактирование email:")
    u1.email = "neemail@gmail.com"
    repo.update(u1)
    print(f"Email изменён на {u1.email}")

    print("\nАвторизация пользователя:")
    auth.sign_in(User(id=None, name="Алеся", login="login", password="password"))
    if auth.is_authorized():
        cur = auth.current_user()
        print(f"Успешно. Пользователь: {cur.name} (id={cur.id})")
    else:
        print("Ошибка авторизации.")

    print("\nАвторизация автоматически:")
    auth2 = AuthService(repo)
    if auth2.is_authorized():
        print(f"Авторизован автоматически: {auth2.current_user().name}")


    print("\n\nСмена пользователя:")
    if auth2.is_authorized():
        auth2.sign_out(auth2.current_user())
    auth2.sign_in(User(id=None, name="", login="ZACHOT", password="228611"))
    if auth2.is_authorized():
        print(f"Успешно. Пользователь: {auth2.current_user().name}")

    print("\nПоиск по логину:")
    found = repo.get_by_login("ZACHOT")
    print(f"   Найден: {found.name if found else 'нет'}")


if __name__ == '__main__':
    demonstrate()