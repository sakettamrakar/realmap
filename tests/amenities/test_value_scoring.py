"""Tests for value-for-money scoring."""
from __future__ import annotations


from cg_rera_extractor.amenities.value_scoring import (
    compute_value_score,
    get_value_bucket,
    DEFAULT_MEDIAN_PRICE,
)


class TestComputeValueScore:
    """Tests for compute_value_score function."""

    def test_returns_none_without_score(self) -> None:
        """Value score requires overall_score."""
        result = compute_value_score(None, 5_000_000)
        assert result is None

    def test_returns_none_without_price(self) -> None:
        """Value score requires price."""
        result = compute_value_score(75.0, None)
        assert result is None

    def test_high_score_low_price_gives_excellent_value(self) -> None:
        """High score + low price should give high value score."""
        # Good score (80) + price below median (2.5M vs 5M median)
        result = compute_value_score(80.0, 2_500_000)
        assert result is not None
        assert result >= 70  # Should be excellent value
        assert get_value_bucket(result) == "excellent"

    def test_low_score_high_price_gives_poor_value(self) -> None:
        """Low score + high price should give low value score."""
        # Low score (30) + price double the median (10M vs 5M median)
        result = compute_value_score(30.0, 10_000_000)
        assert result is not None
        assert result < 40  # Should be poor value
        assert get_value_bucket(result) == "poor"

    def test_average_score_average_price_gives_fair_value(self) -> None:
        """Average score + median price should give moderate value score."""
        # Average score (50) + median price
        result = compute_value_score(50.0, DEFAULT_MEDIAN_PRICE)
        assert result is not None
        assert 40 <= result <= 55  # Should be fair value range
        assert get_value_bucket(result) in ("fair", "good")

    def test_context_can_override_median(self) -> None:
        """Custom median price via context should affect calculation."""
        # Same score and price, but different median
        result_default = compute_value_score(70.0, 5_000_000)
        result_custom = compute_value_score(
            70.0, 5_000_000, context={"median_price": 10_000_000}
        )
        
        # With higher median, same price looks cheaper → better value
        assert result_custom is not None
        assert result_default is not None
        assert result_custom > result_default

    def test_free_project_gives_max_price_factor(self) -> None:
        """Free or very cheap project should have excellent value regardless of score."""
        # Even with mediocre score, free project has value
        result = compute_value_score(50.0, 100)  # Nearly free
        assert result is not None
        # 60% of 50/100 + 40% of ~1.0 = 0.30 + 0.40 = 0.70 → ~70
        assert result >= 65

    def test_score_capped_at_100(self) -> None:
        """Value score should not exceed 100."""
        result = compute_value_score(100.0, 100)  # Perfect score, free
        assert result is not None
        assert result <= 100

    def test_score_floor_at_0(self) -> None:
        """Value score should not go below 0."""
        # Even worst case shouldn't go negative
        result = compute_value_score(0.0, 100_000_000)  # Zero score, very expensive
        assert result is not None
        assert result >= 0


class TestGetValueBucket:
    """Tests for get_value_bucket function."""

    def test_none_returns_unknown(self) -> None:
        assert get_value_bucket(None) == "unknown"

    def test_excellent_threshold(self) -> None:
        assert get_value_bucket(70) == "excellent"
        assert get_value_bucket(85) == "excellent"
        assert get_value_bucket(100) == "excellent"

    def test_good_threshold(self) -> None:
        assert get_value_bucket(55) == "good"
        assert get_value_bucket(65) == "good"
        assert get_value_bucket(69.9) == "good"

    def test_fair_threshold(self) -> None:
        assert get_value_bucket(40) == "fair"
        assert get_value_bucket(50) == "fair"
        assert get_value_bucket(54.9) == "fair"

    def test_poor_threshold(self) -> None:
        assert get_value_bucket(0) == "poor"
        assert get_value_bucket(20) == "poor"
        assert get_value_bucket(39.9) == "poor"
