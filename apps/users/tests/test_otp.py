import pytest
from django.test import override_settings

from core.otp import send_otp, verify_otp


@pytest.mark.django_db
def test_send_then_verify_succeeds():
    code = send_otp("+15550000001")
    assert verify_otp("+15550000001", code) is True


@pytest.mark.django_db
def test_wrong_code_fails():
    send_otp("+15550000002")
    assert verify_otp("+15550000002", "111111") is False


@pytest.mark.django_db
def test_code_is_one_time_use():
    code = send_otp("+15550000003")
    assert verify_otp("+15550000003", code) is True
    assert verify_otp("+15550000003", code) is False


@override_settings(DEBUG=True, OTP_CHEAT_CODE="000000")
@pytest.mark.django_db
def test_cheat_code_accepted_in_debug():
    assert verify_otp("+15550000004", "000000") is True


@override_settings(DEBUG=False, OTP_CHEAT_CODE="000000")
@pytest.mark.django_db
def test_cheat_code_rejected_when_not_debug():
    assert verify_otp("+15550000005", "000000") is False
