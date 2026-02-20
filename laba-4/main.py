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