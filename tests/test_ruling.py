from referee.ruling import parse, quoted, squash, verify, with_penalties

FOUND = [
    {
        "id": "7-3-8",
        "text": "Offensive pass interference. (a) It is a foul, during a forward pass, to push a defender.",
    },
    {"id": "A.R. 9-1-2", "text": "Player A23 clips an opponent."},
]


def test_parse_reads_json_inside_other_text():
    assert parse('Here you go: {"call": "No foul."} done') == {"call": "No foul."}


def test_parse_rejects_bad_json_and_non_objects():
    assert parse("no json here") is None
    assert parse('["7-3-8"]') is None


def test_quote_ignores_punctuation_and_list_markers():
    assert quoted("It is a foul during a forward pass", squash(FOUND[0]["text"]))


def test_quote_with_ellipsis_must_keep_order():
    text = squash(FOUND[0]["text"])
    assert quoted("Offensive pass interference... push a defender", text)
    assert not quoted("push a defender... Offensive pass interference", text)


def test_quote_rejects_words_not_in_the_text():
    assert not quoted("It is a foul to hold a defender", squash(FOUND[0]["text"]))


def test_retrieved_rules_and_approved_rulings_are_verified():
    ruling = {"rules": ["7-3-8", "A.R. 9-1-2"], "quote": "push a defender"}
    assert verify(ruling, FOUND) == ([], True)


def test_rule_not_retrieved_is_unverified():
    ruling = {"rules": ["7-3-8", "9-1-4"], "quote": ""}
    assert verify(ruling, FOUND) == (["9-1-4"], True)


def test_rule_named_only_in_the_explanation_is_unverified():
    ruling = {"rules": ["7-3-8"], "explanation": "See Rule 9-1-4 for targeting."}
    assert verify(ruling, FOUND)[0] == ["9-1-4"]


def test_misquote_is_reported():
    ruling = {"rules": ["7-3-8"], "quote": "the defender is disqualified"}
    assert verify(ruling, FOUND) == ([], False)


def test_penalty_written_elsewhere_in_the_section_is_attached_and_citable():
    pool = [
        {"id": "9-1-16", "text": "Running into the holder is a foul."},
        {"id": "9-1", "text": "PENALTY [ARTICLE 16] - 5 yards from the previous spot."},
    ]
    found = with_penalties(pool[:1], pool)
    assert "5 yards from the previous spot" in found[0]["text"]
    assert verify({"rules": ["9-1-16", "9-1"], "quote": ""}, found) == ([], True)
