from typing import Callable, Any


class classproperty(object):

    def __init__(self, fget: Callable) -> None: ...

    def __get(self, owner_self: Any, owner_cls: Any) -> Any: ...