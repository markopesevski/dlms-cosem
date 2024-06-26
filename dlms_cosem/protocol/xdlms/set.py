from typing import *

import attr

from dlms_cosem import cosem
from dlms_cosem import enumerations as enums
from dlms_cosem.protocol.xdlms.base import AbstractXDlmsApdu
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority
from dlms_cosem.dlms_data import (
    decode_variable_integer,
    encode_variable_integer,
)

"""
Set-Request ::= CHOICE
{
set-request-normal                          [1] IMPLICIT Set-Request-Normal,
set-request-with-first-datablock            [2] IMPLICIT Set-Request-With-First-Datablock,
set-request-with-datablock                  [3] IMPLICIT Set-Request-With-Datablock,
set-request-with-list                       [4] IMPLICIT Set-Request-With-List,
set-request-with-list-and-first-datablock   [5] IMPLICIT Set-Request-With-List-And-First-Datablock
}

Set-Response ::= CHOICE
{
set-response-normal                     [1] IMPLICIT Set-Response-Normal,
set-response-datablock                  [2] IMPLICIT Set-Response-Datablock,
set-response-last-datablock             [3] IMPLICIT Set-Response-Last-Datablock,
set-response-last-datablock-with-list   [4] IMPLICIT Set-Response-Last-Datablock-With-List,
set-response-with-list                  [5] IMPLICIT Set-Response-With-List
}
"""


@attr.s(auto_attribs=True)
class SetRequestNormal(AbstractXDlmsApdu):
    """
    Set-Request-Normal ::= SEQUENCE
    {
        invoke-id-and-priority          Invoke-Id-And-Priority,
        cosem-attribute-descriptor      Cosem-Attribute-Descriptor,
        access-selection                Selective-Access-Descriptor OPTIONAL,
        value                           Data
    }
    """

    TAG: ClassVar[int] = 193
    RESPONSE_TYPE: ClassVar[enums.SetRequestType] = enums.SetRequestType.NORMAL
    cosem_attribute: cosem.CosemAttribute = attr.ib(
        validator=attr.validators.instance_of(cosem.CosemAttribute)
    )
    data: bytes = attr.ib(validator=attr.validators.instance_of(bytes))
    access_selection: Optional[Any] = attr.ib(default=None)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetRequest is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetRequestType(data.pop(0))
        if type_choice is not enums.SetRequestType.NORMAL:
            raise ValueError("The type of the SetRequest is not for a SetRequestNormal")

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )
        cosem_attribute = cosem.CosemAttribute.from_bytes(data[:9])
        data = data[9:]

        has_access_selection = bool(data.pop(0))
        if has_access_selection:
            raise NotImplementedError("Selective access on SET is not implemented")
        else:
            access_selection = None

        return cls(
            cosem_attribute=cosem_attribute,
            data=bytes(data),
            access_selection=access_selection,
            invoke_id_and_priority=invoke_id_and_priority,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.cosem_attribute.to_bytes())
        if self.access_selection:
            out.extend(b"\x01")
            out.extend(self.access_selection.to_bytes())
        else:
            out.extend(b"\x00")
        out.extend(self.data)
        return bytes(out)


@attr.s(auto_attribs=True)
class SetRequestWithFirstBlock(AbstractXDlmsApdu):
    """
    Set-Request-With-First-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority      Invoke-Id-And-Priority,
    cosem-attribute-descriptor  Cosem-Attribute-Descriptor,
    access-selection            [0] IMPLICIT Selective-Access-Descriptor OPTIONAL,
    datablock                   DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE  -- SA == DataBlock for the SET-request, ACTION-request and ACTION-response
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 193
    RESPONSE_TYPE: ClassVar[enums.SetRequestType] = enums.SetRequestType.WITH_FIRST_BLOCK
    cosem_attribute: cosem.CosemAttribute = attr.ib(
        validator=attr.validators.instance_of(cosem.CosemAttribute)
    )
    data: bytes = attr.ib(validator=attr.validators.instance_of(bytes))
    access_selection: Optional[Any] = attr.ib(default=None)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetRequest is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetRequestType(data.pop(0))
        if type_choice is not enums.SetRequestType.WITH_FIRST_BLOCK:
            raise ValueError("The type of the SetRequest is not for a SetRequestWithFirstBlock")

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )
        cosem_attribute = cosem.CosemAttribute.from_bytes(data[:9])
        data = data[9:]

        has_access_selection = bool(data.pop(0))
        if has_access_selection:
            raise NotImplementedError("Selective access on SET is not implemented")
        else:
            access_selection = None

        last_block = bool(data.pop(0))
        if last_block:
            raise ValueError(
                f"Last block set to true in a SetRequestWithFirstBlock. Should only be set "
                f"for a SetRequestWithBlock"
            )

        block_number = int.from_bytes(data[:4], "big")
        if block_number !=1:
            raise ValueError(
                "block_number should be 1 in a SetRequestWithFirstBlock. "
                f"Instead received {block_number}"
            )

        data = data[4:]

        data_length, data = decode_variable_integer(data)
        if data_length != len(data):
            raise ValueError(
                "The octet string in block data is not of the correct length"
            )

        return cls(
            cosem_attribute=cosem_attribute,
            data=bytes(data),
            access_selection=access_selection,
            invoke_id_and_priority=invoke_id_and_priority,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.cosem_attribute.to_bytes())
        if self.access_selection:
            out.extend(b"\x01")
            out.extend(self.access_selection.to_bytes())
        else:
            out.extend(b"\x00")
        out.append(0) # last_block
        out.extend(b'\x00\x00\x00\x01') # block number
        out.extend(encode_variable_integer(len(self.data)))
        out.extend(self.data)
        return bytes(out)


@attr.s(auto_attribs=True)
class SetRequestWithBlock(AbstractXDlmsApdu):
    """
    Set-Request-With-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    datablock               DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE  -- SA == DataBlock for the SET-request, ACTION-request and ACTION-response
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    ...


@attr.s(auto_attribs=True)
class SetRequestWithList(AbstractXDlmsApdu):
    """
    Set-Request-With-List ::= SEQUENCE
    {
    invoke-id-and-priority      Invoke-Id-And-Priority,
    attribute-descriptor-list   SEQUENCE OF Cosem-Attribute-Descriptor-With-Selection,
    value-list                  SEQUENCE OF Data
    }

    Cosem-Attribute-Descriptor-With-Selection ::= SEQUENCE
    {
    cosem-attribute-descriptor   Cosem-Attribute-Descriptor,
    access-selection             Selective-Access-Descriptor OPTIONAL
    }
    """

    ...


@attr.s(auto_attribs=True)
class SetRequestWithListFirstBlock(AbstractXDlmsApdu):
    """
    Set-Request-With-List-And-First-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    attribute-descriptor-list  SEQUENCE OF Cosem-Attribute-Descriptor-With-Selection,
    datablock DataBlock-SA
    }

    Cosem-Attribute-Descriptor-With-Selection ::= SEQUENCE
    {
    cosem-attribute-descriptor   Cosem-Attribute-Descriptor,
    access-selection             Selective-Access-Descriptor OPTIONAL
    }

    DataBlock-SA ::= SEQUENCE  -- SA == DataBlock for the SET-request, ACTION-request and ACTION-response
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }

    """

    ...


@attr.s(auto_attribs=True)
class SetRequestFactory:
    """
    The factory will parse the SetRequest and return either a SetRequest type class
    """

    TAG: ClassVar[int] = 193

    @staticmethod
    def from_bytes(source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != SetRequestFactory.TAG:
            raise ValueError(
                f"Tag for GET request is not correct. Got {tag}, should be "
                f"{SetRequestFactory.TAG}"
            )
        request_type = enums.SetRequestType(data.pop(0))
        if request_type == enums.SetRequestType.NORMAL:
            return SetRequestNormal.from_bytes(source_bytes)
        elif request_type == enums.SetRequestType.WITH_FIRST_BLOCK:
            return SetRequestWithFirstBlock.from_bytes(source_bytes)
        elif request_type == enums.SetRequestType.WITH_BLOCK:
            return SetRequestWithBlock.from_bytes(source_bytes)
        else:
            raise NotImplementedError("Unsupported set subtype: {request_type}")


@attr.s(auto_attribs=True)
class SetResponseNormal(AbstractXDlmsApdu):
    """
    Set-Response-Normal ::= SEQUENCE
    {
        invoke-id-and-priority Invoke-Id-And-Priority,
        result  Data-Access-Result
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.NORMAL
    result: enums.DataAccessResult = attr.ib(
        validator=attr.validators.instance_of(enums.DataAccessResult)
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.NORMAL:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseNormal"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        result = enums.DataAccessResult(data.pop(0))

        return cls(result=result, invoke_id_and_priority=invoke_id_and_priority)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(self.result.value)
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseWithBlock(AbstractXDlmsApdu):
    """
    Set-Response-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    block-number            Unsigned32
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.WITH_BLOCK
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    block_number: int = attr.ib(validator=attr.validators.instance_of(int), default=0)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.WITH_BLOCK:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseWithBlock"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        block_number = int.from_bytes(data[:4], "big")

        return cls(invoke_id_and_priority=invoke_id_and_priority, block_number=block_number)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.block_number.to_bytes(4, 'big'))
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseLastBlock(AbstractXDlmsApdu):
    """
    Set-Response-Last-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    result                  Data-Access-Result,
    block-number            Unsigned32
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.WITH_LAST_BLOCK
    result: enums.DataAccessResult = attr.ib(
        validator=attr.validators.instance_of(enums.DataAccessResult)
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    block_number: int = attr.ib(validator=attr.validators.instance_of(int), default=0)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.WITH_LAST_BLOCK:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseLastBlock"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        result = enums.DataAccessResult(data.pop(0))
        block_number = int.from_bytes(data[:4], "big")

        return cls(result=result, invoke_id_and_priority=invoke_id_and_priority, block_number=block_number)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(self.result.value)
        out.extend(self.block_number.to_bytes(4, 'big'))
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseLastBlockWithList(AbstractXDlmsApdu):
    """
    Set-Response-Last-Datablock-With-List ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    result                  SEQUENCE OF Data-Access-Result,
    block-number            Unsigned32
    }
    """

    ...


@attr.s(auto_attribs=True)
class SetResponseWithList(AbstractXDlmsApdu):
    """
    Set-Response-With-List ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    result                  SEQUENCE OF Data-Access-Result,
    }
    """

    ...


@attr.s(auto_attribs=True)
class SetResponseFactory:
    """
    The factory will parse the SetResponse and return a SetResponse type class
    """

    TAG: ClassVar[int] = 197

    @staticmethod
    def from_bytes(source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != SetResponseFactory.TAG:
            raise ValueError(
                f"Tag for Set response is not correct. Got {tag}, should be "
                f"{SetResponseFactory.TAG}"
            )
        request_type = enums.SetResponseType(data.pop(0))
        if request_type == enums.SetResponseType.NORMAL:
            return SetResponseNormal.from_bytes(source_bytes)
        elif request_type == enums.SetResponseType.WITH_BLOCK:
            return SetResponseWithBlock.from_bytes(source_bytes)
        elif request_type == enums.SetResponseType.WITH_LAST_BLOCK:
            return SetResponseLastBlock.from_bytes(source_bytes)
        else:
            raise NotImplementedError(f"not implemented {request_type}")
