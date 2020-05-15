import logging

logger = logging.getLogger("logs")


class DataValidator:
    @staticmethod
    def validate(table, tenpai_player, player, second_player, third_player):
        assert len(tenpai_player.waiting) > 0, logger.error("Tenpai player doesnt have waiting")
        assert len(table.dora_indicators) <= 4, logger.error("Too many dora indicators")

        DataValidator._validate_melds(tenpai_player.melds)
        DataValidator._validate_melds(player.melds)
        DataValidator._validate_melds(second_player.melds)
        DataValidator._validate_melds(third_player.melds)

        DataValidator._validate_closed_hand(tenpai_player.closed_hand)
        DataValidator._validate_closed_hand(player.closed_hand)
        DataValidator._validate_closed_hand(second_player.closed_hand)
        DataValidator._validate_closed_hand(third_player.closed_hand)

        assert len(tenpai_player.closed_hand) < 14, logger.error(
            f"Player hand too big len={tenpai_player.closed_hand}"
        )

    @staticmethod
    def _validate_melds(melds):
        assert len(melds) <= 4, logger.error(f"Too many melds sets len={len(melds)}")

    @staticmethod
    def _validate_closed_hand(closed_hand):
        assert len(closed_hand) > 0 <= 14, logger.error(f"Too many tiles in hand len={len(closed_hand)}")
