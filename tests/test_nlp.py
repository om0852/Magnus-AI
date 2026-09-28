from nlp.inference.engine import InferenceEngine

def test_nlp_rule_parser():
    engine = InferenceEngine()

    # Open app
    res1 = engine.parse("open chrome")
    assert res1["intent"] == "OPEN_APP"
    assert res1["entities"]["application"] == "chrome"

    # Close app
    res2 = engine.parse("close notepad")
    assert res2["intent"] == "CLOSE_APP"
    assert res2["entities"]["application"] == "notepad"

    # Search web
    res3 = engine.parse("search youtube for react tutorials")
    assert res3["intent"] == "SEARCH_WEB"
    assert res3["entities"]["site"] == "youtube"
    assert res3["entities"]["query"] == "react tutorials"

    # Volume change
    res4 = engine.parse("increase volume by 20 percent")
    assert res4["intent"] == "CHANGE_VOLUME"
    assert res4["entities"]["amount"] == 20
    assert res4["entities"]["direction"] == "increase"

    # Unknown command
    res5 = engine.parse("abracadabra 12345 xyz")
    assert res5["intent"] == "UNKNOWN"
