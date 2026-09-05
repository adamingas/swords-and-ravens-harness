from raven_harness.game.codec import decode_message, encode_message


def test_protocol_codec_round_trips() -> None:
    message = {"type": "choose-house", "house": "stark", "password": "winter"}
    assert decode_message(encode_message(message)) == message
