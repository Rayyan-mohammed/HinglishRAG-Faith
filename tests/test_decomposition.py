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


def test_splits_on_aur():
    answer = "PM-KISAN mein har saal 6000 rupees milte hain aur yeh amount teen installments mein aata hai."
    claims = decompose(answer)
    assert len(claims) == 2
    assert claims[0] == "PM-KISAN mein har saal 6000 rupees milte hain"
    assert claims[1] == "yeh amount teen installments mein aata hai"


def test_splits_on_kyunki():
    answer = "Aapka application reject ho sakta hai kyunki Aadhaar number match nahi hua."
    claims = decompose(answer)
    assert len(claims) == 2


def test_multi_sentence_multi_connector_answer():
    answer = (
        "Ayushman Bharat card se aapko 5 lakh tak ka free treatment milta hai. "
        "Yeh sirf empanelled hospitals mein valid hai, lekin private hospitals bhi is "
        "list mein aate hain."
    )
    claims = decompose(answer)
    assert len(claims) == 3


def test_known_limitation_noun_phrase_connector():
    """'aur' joining two nouns inside one clause (not two separate claims) still gets
    split into two fragments — a known weakness of the rule-based splitter, tracked as
    ADR-003 in docs/problems_and_decisions.md. Documented here rather than hidden."""
    answer = "Yeh scheme government aur private hospitals dono mein valid hai."
    claims = decompose(answer)
    assert len(claims) == 2
    assert claims[0] == "Yeh scheme government"
    assert claims[1] == "private hospitals dono mein valid hai"


def test_single_claim_no_connector():
    answer = "Scholarship ke liye income certificate zaroori hai."
    claims = decompose(answer)
    assert claims == ["Scholarship ke liye income certificate zaroori hai"]


def test_claims_have_no_trailing_punctuation():
    answer = "Aapko form fill karna hoga, aur documents attach karne honge."
    claims = decompose(answer)
    assert all(not c.endswith((",", ".")) for c in claims)


def test_drops_degenerate_bare_entity_fragments():
    """Real case found in P-008's evidence-text diagnosis (Q13/Q15): two connectors close
    together strand a short place-name list as its own "claim" with no checkable content —
    e.g. two prior sentence connectors leave "Assam, Meghalaya" isolated between them."""
    answer = "Xyz ke liye yeh rule hai, lekin Assam, Meghalaya, aur Jammu ke liye alag hai."
    claims = decompose(answer)
    assert claims == ["Xyz ke liye yeh rule hai", "Jammu ke liye alag hai"]


def test_keeps_short_but_meaningful_claims():
    """The fragment filter must not be so aggressive it drops real short claims."""
    answer = "Bank account details."
    assert decompose(answer) == ["Bank account details"]


def test_rs_abbreviation_does_not_split_sentence():
    """'Rs.' followed by an amount was being mistaken for a sentence boundary, producing
    a lone 'Rs' fragment — found running decompose() on real generated answers (P-002 in
    docs/problems_and_decisions.md)."""
    answer = (
        "EWS households ke liye annual income upto Rs. 3.00 lakhs hai, aur LIG households "
        "ke liye annual income Rs. 3.00 lakhs se Rs. 6.00 lakhs ke beech hai."
    )
    claims = decompose(answer)
    assert not any(c == "Rs" for c in claims)
