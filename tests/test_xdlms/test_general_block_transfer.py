from dlms_cosem.protocol.xdlms.general_block_transfer import GeneralBlockTransfer


def test_generate_gbt():
    pdu = (
        b"\xE0"
        + bytes([True << 7 | False << 6 | 3])
        + b"\x00\x04"
        + b"\x00\x05"
        + b"\x03"
        + b"abc"
    )
    parsed = GeneralBlockTransfer(
        last_block=True,
        streaming=False,
        window=3,
        block_number=4,
        block_ack=5,
        block_data=b"abc",
    )
    assert (pdu) == parsed.to_bytes()
    assert parsed == GeneralBlockTransfer.from_bytes(pdu)
