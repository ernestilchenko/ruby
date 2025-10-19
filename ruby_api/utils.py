from PyQt5.QtCore import QVariant


def qvariant_to_python(value):
    if isinstance(value, QVariant):
        if value.isNull():
            return None
        return value.value()
    return value
