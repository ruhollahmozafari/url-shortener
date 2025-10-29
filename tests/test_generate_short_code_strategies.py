"""
Tests for short code generation strategies.
"""
from shortener_app.services.short_code_strategies import (
    RandomShortCodeStrategy,
    Base62ShortCodeStrategy
)
from shortener_app.services.short_code_factory import (
    ShortCodeFactory,
    ShortCodeStrategyType
)



class TestBase62Strategy:
    """Test Base62 encoding strategy"""
    
    def test_generates_correct_length(self, db_session):
        """Test that Base62 strategy generates codes of correct length"""
        strategy = Base62ShortCodeStrategy(salt=1000, max_length=5)
        
        code = strategy.generate(url_id=1, db_session=db_session)
        
        assert len(code) <= 5

    
    def test_same_id_same_code(self, db_session):
        """Test that same ID generates same code (deterministic)"""
        strategy = Base62ShortCodeStrategy(salt=1000, max_length=5)
        
        code1 = strategy.generate(url_id=123, db_session=db_session)
        code2 = strategy.generate(url_id=123, db_session=db_session)
        
        assert code1 == code2
    
    def test_different_id_different_code(self, db_session):
        """Test that different IDs generate different codes"""
        strategy = Base62ShortCodeStrategy(salt=1000, max_length=5)
        
        code1 = strategy.generate(url_id=1, db_session=db_session)
        code2 = strategy.generate(url_id=2, db_session=db_session)
        code3 = strategy.generate(url_id=3, db_session=db_session)
        
        assert code1 != code2
        assert code2 != code3
        assert code1 != code3
    
    def test_obfuscation_with_salt(self, db_session):
        """Test that salt obfuscates the sequence"""
        strategy_no_salt = Base62ShortCodeStrategy(salt=0, max_length=5)
        strategy_with_salt = Base62ShortCodeStrategy(salt=1000, max_length=5)
        
        code_no_salt = strategy_no_salt.generate(url_id=1, db_session=db_session)
        code_with_salt = strategy_with_salt.generate(url_id=1, db_session=db_session)
        
        # Codes should be different due to salt
        assert code_no_salt != code_with_salt


class TestShortCodeFactory:
    """Test strategy factory"""
    
    def test_creates_random_strategy(self):
        """Test factory creates random strategy"""
        strategy = ShortCodeFactory.create_strategy(ShortCodeStrategyType.RANDOM)
        assert isinstance(strategy, RandomShortCodeStrategy)
    
    def test_creates_base62_strategy(self):
        """Test factory creates Base62 strategy"""
        strategy = ShortCodeFactory.create_strategy(ShortCodeStrategyType.BASE62)
        assert isinstance(strategy, Base62ShortCodeStrategy)

    def test_creates_default_from_settings(self):
        """Test factory uses settings when no type specified"""
        strategy = ShortCodeFactory.create_strategy()
        # Should create whatever is configured in settings (base62 by default)
        assert strategy is not None


from shortener_app.services.short_code_strategies import Base62ShortCodeStrategy
from shortener_app.models.url import URL


class TestBase62EdgeCases:
    """Test Base62 strategy with edge cases and high volumes"""

    def test_first_url(self, db_session):
        """Test the very first URL (ID=1)"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        code = strategy.generate(url_id=1, db_session=db_session)

        # Should generate valid code
        assert len(code) <= 5
        assert code.isalnum()
        print(f"ID 1: {code}")

    def test_early_ids(self, db_session):
        """Test first 100 URLs"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        codes = set()
        for url_id in range(1, 101):
            code = strategy.generate(url_id, db_session)
            codes.add(code)
            assert len(code) <= 5

        # All should be unique
        assert len(codes) == 100
        print(f"IDs 1-100: All unique, sample: {list(codes)[:5]}")

    def test_thousand_urls(self, db_session):
        """Test at 1,000 URLs"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        code = strategy.generate(url_id=1000, db_session=db_session)

        assert len(code) <= 5
        print(f"ID 1,000: {code}")

    def test_ten_thousand_urls(self, db_session):
        """Test at 10,000 URLs"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        code = strategy.generate(url_id=10000, db_session=db_session)

        assert len(code) <= 5
        print(f"ID 10,000: {code}")

    def test_hundred_thousand_urls(self, db_session):
        """Test at 100,000 URLs"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        code = strategy.generate(url_id=100000, db_session=db_session)

        assert len(code) <= 5
        print(f"ID 100,000: {code}")

    def test_one_million_urls(self, db_session):
        """Test at 1,000,000 URLs"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        code = strategy.generate(url_id=1000000, db_session=db_session)

        assert len(code) <= 5
        print(f"ID 1,000,000: {code}")

    def test_ten_million_urls(self, db_session):
        """Test at 10,000,000 URLs - Should start failing with small salt"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        # This might exceed 5 characters depending on salt
        try:
            code = strategy.generate(url_id=10000000, db_session=db_session)
            assert len(code) <= 5
            print(f"ID 10,000,000: {code} (still fits!)")
        except ValueError as e:
            print(f"ID 10,000,000: Exceeded max length as expected: {e}")
            # This is expected behavior - need larger salt or max_length

    def test_capacity_calculation(self, db_session):
        """Test and document capacity limits"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        # Calculate theoretical capacity
        # Base62^5 = 62^5 = 916,132,832 possible codes
        # But we need to account for salt offset

        # With salt=1256, we can handle IDs from 1 to approximately:
        # max_id ≈ (62^5) - salt - 1

        print("\n" + "=" * 60)
        print("Capacity Analysis:")
        print("=" * 60)
        print(f"Base62 charset: 62 characters")
        print(f"Max length: {strategy.max_length} characters")
        print(f"Total possible codes: 62^{strategy.max_length} = {62 ** strategy.max_length:,}")
        print(f"Salt: {strategy.salt}")
        print(f"Usable capacity: ~{(62 ** strategy.max_length) - strategy.salt:,} URLs")
        print("=" * 60)

    def test_uniqueness_at_scale(self, db_session):
        """Test uniqueness with sample of large IDs"""
        strategy = Base62ShortCodeStrategy(salt=1256, max_length=5)

        # Test IDs at different scales
        test_ids = [1, 100, 1000, 10000, 100000, 500000, 1000000]

        codes = {}
        for url_id in test_ids:
            try:
                code = strategy.generate(url_id, db_session)
                codes[url_id] = code
                print(f"  ID {url_id:>10,} → {code}")
            except ValueError as e:
                print(f"  ID {url_id:>10,} → ERROR: Exceeded max length")

        # All generated codes should be unique
        unique_codes = set(codes.values())
        assert len(unique_codes) == len(codes)
        print(f"\n  ✅ All {len(codes)} codes are unique")

    def test_salt_impact(self, db_session):
        """Test how different salts affect output"""
        test_id = 1

        salts = [0, 100, 1000, 10000, 100000]

        print("\n" + "=" * 60)
        print("Salt Impact Analysis:")
        print("=" * 60)

        for salt in salts:
            strategy = Base62ShortCodeStrategy(salt=salt, max_length=5)
            code = strategy.generate(test_id, db_session)
            obfuscated = test_id + salt
            print(f"  Salt {salt:>6}: ID 1 → {obfuscated:>6} → '{code}'")
        print("=" * 60)
