"""Deterministic merchant counteroffer policy for the modal commerce dialog."""

from engine.negotiation import evaluate_counteroffer, merchant_haggle_policy


def test_kelem_will_discount_mundane_stock_by_up_to_twenty_percent():
    policy = merchant_haggle_policy("kelem", category="mundane")
    assert policy.minimum_price(200) == 160


def test_low_offer_gets_merchants_floor_as_counter():
    result = evaluate_counteroffer(
        ask_cp=200, offered_cp=100,
        policy=merchant_haggle_policy("kelem", category="mundane"),
    )
    assert not result.accepted
    assert result.counter_cp == 160


def test_offer_inside_flexible_range_is_accepted():
    result = evaluate_counteroffer(
        ask_cp=200, offered_cp=180,
        policy=merchant_haggle_policy("kelem", category="mundane"),
    )
    assert result.accepted
    assert result.agreed_cp == 180

