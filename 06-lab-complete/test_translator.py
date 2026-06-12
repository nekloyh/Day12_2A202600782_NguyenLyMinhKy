"""Small dependency-free regression test for the translation domain logic."""
from app.token_guard import TokenGuard
from app.translator import normalize, translate


def run():
    assert normalize("Cảm ơn!") == "cam on"

    hotel, usage = translate("Tôi muốn đặt phòng", "hotel")
    assert hotel["translation"] == "객실을 예약하고 싶습니다."
    assert hotel["honorific_level"] == "formal-polite"
    assert "싶습니다" in hotel["explanation"]
    assert usage["provider"] == "phrasebook"

    restaurant, _ = translate("Cho tôi xem thực đơn", "restaurant")
    assert "주시겠어요" in restaurant["translation"]

    fallback, _ = translate("Tôi bị thất lạc hành lý", "emergency")
    assert "도움이 필요합니다" in fallback["translation"]
    assert "Tôi bị thất lạc hành lý" in fallback["cultural_note"]

    guard = TokenGuard()
    reservation = guard.reserve("test-user", "Xin chào")
    usage = guard.commit(reservation, input_tokens=40, output_tokens=20)
    assert usage["user_monthly_used_tokens"] == 60
    assert usage["global_monthly_used_tokens"] == 60
    assert usage["global_monthly_limit_tokens"] == 100000

    print("5 translator and token-guard checks passed")


if __name__ == "__main__":
    run()
