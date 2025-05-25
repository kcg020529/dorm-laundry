from celery import shared_task
from .models import Reservation, PushSubscription
from django.conf import settings
from pywebpush import webpush, WebPushException
import json

@shared_task
def send_reservation_reminder(reservation_id, when):
    try:
        reservation = Reservation.objects.get(id=reservation_id)

        # 메시지 분기
        if when == '10분 전':
            body = f"{reservation.start_time.strftime('%H:%M')}에 예약하신 세탁기 이용 시간이 10분 남았습니다."
        else:
            body = "지금 예약하신 세탁기를 이용할 시간입니다."

        payload = {
            "title": "[세탁기 예약 알림]",
            "body": body,
            "url": "/mypage/reservations/"
        }

        subs = PushSubscription.objects.filter(user=reservation.user)
        if not subs.exists():
            return "구독 정보 없음, 푸시 스킵"

        vapid_kwargs = {
            "vapid_private_key": settings.WEBPUSH_SETTINGS["VAPID_PRIVATE_KEY"],
            "vapid_claims": settings.WEBPUSH_SETTINGS["VAPID_CLAIMS"],
        }
        for sub in subs:
            try:
                webpush(
                    subscription_info=sub.subscription_info,
                    data=json.dumps(payload),
                    **vapid_kwargs
                )
            except WebPushException:
                sub.delete()

        return "푸시 알림 전송 완료"

    except Reservation.DoesNotExist:
        return "해당 예약이 없습니다."
    except Exception as e:
        return str(e)