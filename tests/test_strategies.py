"""
Tests for wallet_system.strategies.

These are deliberately independent of MerchantWallet — a strategy is a
standalone object with its own contract (given an amount, return a fee),
so it should be testable without constructing a wallet at all.
"""
import pytest

from wallet_system.strategies import (
    FeeStrategy,
    FlatFeeStrategy,
    TieredFeeStrategy,
    NoFeeStrategy,
)


# ---------------------------------------------------------------------------
# FlatFeeStrategy
# ---------------------------------------------------------------------------

def test_flat_fee_default_rate_is_1_5_percent():
    strategy = FlatFeeStrategy()
    assert strategy.calculate_fee(1000) == 15.0


def test_flat_fee_custom_rate():
    strategy = FlatFeeStrategy(rate=0.02)
    assert strategy.calculate_fee(1000) == 20.0


def test_flat_fee_rounds_to_two_decimals():
    strategy = FlatFeeStrategy(rate=0.015)
    assert strategy.calculate_fee(333) == round(333 * 0.015, 2)


@pytest.mark.parametrize("bad_rate", [-0.1, 1.1])
def test_flat_fee_rejects_rate_outside_zero_to_one(bad_rate):
    with pytest.raises(ValueError):
        FlatFeeStrategy(rate=bad_rate)


# ---------------------------------------------------------------------------
# TieredFeeStrategy
# ---------------------------------------------------------------------------

def test_tiered_fee_uses_low_rate_below_threshold():
    strategy = TieredFeeStrategy(low_rate=0.02, high_rate=0.01, threshold=10_000)
    assert strategy.calculate_fee(5_000) == 100.0  # 2% of 5,000


def test_tiered_fee_uses_high_rate_above_threshold():
    strategy = TieredFeeStrategy(low_rate=0.02, high_rate=0.01, threshold=10_000)
    assert strategy.calculate_fee(20_000) == 200.0  # 1% of 20,000


def test_tiered_fee_at_exact_threshold_uses_low_rate():
    """Boundary case: threshold itself is NOT > threshold, so low_rate applies."""
    strategy = TieredFeeStrategy(low_rate=0.02, high_rate=0.01, threshold=10_000)
    assert strategy.calculate_fee(10_000) == 200.0  # 2% of 10,000, not 1%


def test_tiered_fee_one_unit_above_threshold_uses_high_rate():
    strategy = TieredFeeStrategy(low_rate=0.02, high_rate=0.01, threshold=10_000)
    fee = strategy.calculate_fee(10_000.01)
    assert fee == round(10_000.01 * 0.01, 2)


# ---------------------------------------------------------------------------
# NoFeeStrategy
# ---------------------------------------------------------------------------

def test_no_fee_strategy_always_returns_zero():
    strategy = NoFeeStrategy()
    assert strategy.calculate_fee(1_000_000) == 0.0
    assert strategy.calculate_fee(1) == 0.0


# ---------------------------------------------------------------------------
# All strategies share the same contract
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("strategy", [
    FlatFeeStrategy(),
    TieredFeeStrategy(),
    NoFeeStrategy(),
])
def test_all_strategies_are_fee_strategy_instances(strategy):
    assert isinstance(strategy, FeeStrategy)


@pytest.mark.parametrize("strategy", [
    FlatFeeStrategy(),
    TieredFeeStrategy(),
    NoFeeStrategy(),
])
def test_all_strategies_return_fee_not_exceeding_amount(strategy):
    """A fee should never exceed the amount it's deducted from — otherwise
    a deposit could reduce the balance, which is a business-rule
    violation no strategy should be able to produce."""
    fee = strategy.calculate_fee(1000)
    assert 0 <= fee <= 1000