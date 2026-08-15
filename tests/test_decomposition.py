from src.decomposition import decompose


def test_splits_on_sentence_boundary():
    answer = "Aapka application 15 din mein process hoga. Aadhaar copy chahiye hogi."
    claims = decompose(answer)
    assert len(claims) == 2


def test_splits_on_connector_word():
    answer = "Aapka application 15 din mein process ho jayega, but aapko Aadhaar copy submit karni hogi."
    claims = decompose(answer)
    assert len(claims) == 2
    assert not claims[1].lower().startswith("but")


def test_ignores_empty_input():
    assert decompose("") == []
