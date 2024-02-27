from typing import ClassVar

import attr
from dlms_cosem.protocol.xdlms.base import AbstractXDlmsApdu


@attr.s(auto_attribs=True)
class GeneralBlockTransfer(AbstractXDlmsApdu):
    TAG: ClassVar[int] = 224
    last_block: bool
    streaming: bool
    window: int
    block_number: int
    block_ack: int
    block_data: bytes

    # TODO: add attrs.validator equivalent to:
    # assert 0 <= window < 2**6
    # assert 0 <= block_number < 2**16
    # assert 0 <= block_ack < 2**16

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(f"Tag is not correct. Should be {cls.TAG} but got {tag}")

        block_control = data.pop(0)
        last_block = bool(block_control & 0b10000000)
        streaming = bool(block_control & 0b01000000)
        window = block_control & 0b00111111

        block_number = int.from_bytes(data[:2], "big")
        del data[:2]
        block_ack = int.from_bytes(data[:2], "big")
        del data[:2]

        length = data.pop(0)
        block_data = data[:length]
        del data[:length]
        assert not data

        return cls(
            last_block=last_block,
            streaming=streaming,
            window=window,
            block_number=block_number,
            block_ack=block_ack,
            block_data=block_data,
        )

    def to_bytes(self):
        return (
            b"\xE0"
            + bytes([self.last_block << 7 | self.streaming << 6 | self.window])
            + self.block_number.to_bytes(2, "big")
            + self.block_ack.to_bytes(2, "big")
            + len(self.block_data).to_bytes(1, "big")
            + self.block_data
        )
