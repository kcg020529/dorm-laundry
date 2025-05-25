document.getElementById('reserveButton').addEventListener('click', function() {
    alert("세탁기가 예약되었습니다!");
  });
  
  document.addEventListener('DOMContentLoaded', () => {
  // 예약 버튼이 여러 개일 경우, forEach 로 일괄 바인딩
  document.querySelectorAll('.reserve-button').forEach(btn => {
    btn.addEventListener('click', async () => {
      const machineId = btn.dataset.machineId;
      const startTime = btn.dataset.startTime; // ISO 문자열
      const endTime   = btn.dataset.endTime;
      btn.disabled = true;
      btn.textContent = '예약 중...';

      try {
        const res = await fetch('/laundry/reservations/create/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
          },
          body: JSON.stringify({
            machine_id: machineId,
            start_time: startTime,
            end_time: endTime,
          })
        });
        const data = await res.json();

        if (res.ok) {
          alert('예약이 완료되었습니다!');
          // UI 갱신: 상태 변경 혹은 페이지 새로고침
          btn.textContent = '예약 완료';
          btn.classList.add('disabled');
        } else {
          alert('예약 실패: ' + (data.error || '알 수 없는 오류'));
          btn.disabled = false;
          btn.textContent = '예약하기';
        }
      } catch (err) {
        console.error(err);
        alert('네트워크 오류가 발생했습니다.');
        btn.disabled = false;
        btn.textContent = '예약하기';
      }
    });
  });
});