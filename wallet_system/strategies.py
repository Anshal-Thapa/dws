from abc import ABC, abstractmethod


class FeeStrategy(ABC):
    @abstractmethod
    def calculate_fee(self, amount: float) -> float:
        ...

class FlatFeeStrategy(FeeStrategy):
    def __init__(self, rate: float = 0.015) -> None:
        if not (0 <= rate <= 1):
            raise ValueError(f"rate must be between 0 and 1, got {rate}")
        self.rate = rate

    def calculate_fee(self, amount: float) -> float:
        return round(amount * self.rate, 2)


class TieredFeeStrategy(FeeStrategy):
    '''
    Low rate till threshhold meets to apply lower fee rate from higher amount
    '''
    def __init__(
        self,
        low_rate: float = 0.02,
        high_rate: float = 0.01,
        threshold: float = 10_000.0,
    ) -> None:
        self.low_rate = low_rate
        self.high_rate = high_rate
        self.threshold = threshold

    def calculate_fee(self, amount: float) -> float:
        rate = self.high_rate if amount > self.threshold else self.low_rate
        return round(amount * rate, 2)


class NoFeeStrategy(FeeStrategy):
    """For promotional periods or fee-exempt merchant accounts."""

    def calculate_fee(self, amount: float) -> float:
        return 0.0