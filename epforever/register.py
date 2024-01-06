from typing import Literal, Union


class Register:
    def __init__(
        self,
        id: int,
        fieldname: str,
        register_id: int,
        datatype: str,
        divider: int
    ):
        self.id = id
        self.fieldname = fieldname
        self.register_id = register_id
        self.datatype = datatype
        self.divider = divider
        self.kind: Literal['lowhigh', 'simple'] = None
        self.value: Union[str, bytes] = ''
        self.lsb: str = ''
        self.msb: str = ''
        self.type: str = 'state'

    def set_definition(
        self,
        kind: Literal['lowhigh', 'simple'],
        value: str = '',
        lsb: str = '',
        msb: str = ''
    ):
        if (kind == 'lowhigh' and not lsb) or (kind == 'lowhigh' and not msb):
            raise ValueError(
                "For lowhigh kind, both lsb and msb must be provided."
            )
        elif (kind == 'simple' and not value):
            raise ValueError("For simple kind, a value must be provided.")

        self.kind = kind
        self.value = value
        self.lsb = lsb
        self.msb = msb
