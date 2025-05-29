document.addEventListener('DOMContentLoaded', () => {
  // 예약 버튼이 여러 개일 경우, forEach 로 일괄 바인딩
  document.querySelectorAll('.reserve-button').forEach(btn => {
      btn.addEventListener('click', async () => {
          const machineId = btn.dataset.machineId;
          const startTime = btn.dataset.startTime; // ISO 문자열
          const endTime = btn.dataset.endTime;
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

  // 5초마다 실시간 상태 업데이트
  async function updateMachineStatus() {
      try {
          const res = await fetch('/laundry/machines/status/');
          if (!res.ok) {
              console.error('서버 응답 오류', res.status);
              return;
          }
          const data = await res.json();
          data.forEach(machine => {
              const statusEl = document.querySelector(`#machine-${machine.machine_id}`);
              const btnEl = document.querySelector(`#reserve-btn-${machine.machine_id}`);
              const cardEl = document.querySelector(`#machine-card-${machine.machine_id}`);

              if (statusEl) {
                  statusEl.textContent = machine.is_in_use ? '❌ 사용 중' : '✅ 사용 가능';
                  statusEl.classList.toggle('in-use', machine.is_in_use);
                  statusEl.classList.toggle('available', !machine.is_in_use);
              }

              if (btnEl) {
                  if (machine.is_in_use) {
                      btnEl.textContent = '예약 불가';
                      btnEl.disabled = true;
                      btnEl.classList.add('disabled');
                  } else {
                      btnEl.textContent = '지금 예약';
                      btnEl.disabled = false;
                      btnEl.classList.remove('disabled');
                  }
              }

              if (cardEl) {
                  cardEl.classList.toggle('machine-in-use', machine.is_in_use);
                  cardEl.classList.toggle('machine-available', !machine.is_in_use);
              }
          });
      } catch (error) {
          console.error('상태 갱신 중 오류 발생', error);
      }
  }

  setInterval(updateMachineStatus, 5000);
});
