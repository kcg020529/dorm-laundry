from celery import shared_task
from .models import Reservation, PushSubscription
from django.conf import settings
from pywebpush import webpush, WebPushException
import json

@shared_task
def send_reservation_reminder(reservation_id, when):
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        user = reservation.user
        # 해당 유저의 브라우저 구독 정보 가져오기
        subs = PushSubscription.objects.filter(user=user)
        if not subs.exists():
            return "구독 정보 없음, 푸시 스킵"

        vapid_kwargs = {
            "vapid_private_key": settings.WEBPUSH_SETTINGS["VAPID_PRIVATE_KEY"],
            "vapid_claims": settings.WEBPUSH_SETTINGS["VAPID_CLAIMS"],
        }
        payload = {
            "title": "[세탁기 예약 알림]",
            "body": f"{reservation.start_time.strftime('%H:%M')}에 예약하신 세탁기 이용 시간이 10분 남았습니다.",
            "url": "/mypage/reservations/",  # 사용자가 클릭 시 이동할 URL
        }

        for sub in subs:
            try:
                webpush(
                    subscription_info=sub.subscription_info,
                    data=json.dumps(payload),
                    **vapid_kwargs
                )
            except WebPushException as exc:
                # 실패 시 구독 삭제 또는 로깅
                sub.delete()
                # 로깅: print(exc) 등
        return "푸시 알림 전송 완료"

    except Reservation.DoesNotExist:
        return "해당 예약이 없습니다."
    except Exception as e:
        return str(e)