import Icon from '../../shared/ui/Icon.jsx';
import { chosen, credits, days, time, overlaps } from '../courses/courses.js';
export default function Schedule({ state, previewId, onPrint }) {
  const selected = chosen(state),
    preview = state.courses.find((c) => c.id === previewId && !state.enrolledIds.includes(c.id));
  const warning = preview && overlaps(preview, selected);
  const blocks = [
    ...selected.map((course) => ({ course, preview: false })),
    ...(preview ? [{ course: preview, preview: true }] : []),
  ];
  return (
    <section className="panel schedule-panel">
      <div className="panel-heading">
        <div>
          <h2>
            나의 시간표 <span className="small-pill">미리보기</span>
          </h2>
          <p>2026학년도 2학기</p>
        </div>
        <button className="icon-button" aria-label="시간표 인쇄" onClick={onPrint}>
          <Icon name="download" />
        </button>
      </div>
      <div className="schedule-legend">
        <span>
          <i /> 신청 완료
        </span>
        <span>
          <i /> 미리보기
        </span>
        <b>{credits(state)}학점</b>
      </div>
      <div className="timetable">
        <div className="day-header">
          <span />
          {days.map((day) => (
            <span key={day}>{day}</span>
          ))}
        </div>
        <div className="schedule-body">
          <div className="time-labels">
            {Array.from({ length: 9 }, (_, i) => (
              <span key={i} style={{ top: `${(i / 9) * 100}%` }}>
                {String(i + 9).padStart(2, '0')}
              </span>
            ))}
          </div>
          <div className="week-grid">
            {blocks.flatMap(({ course, preview: isPreview }) =>
              course.meetings.map((m, i) => (
                <div
                  key={`${course.id}-${i}`}
                  className={`course-block ${course.color} ${isPreview ? 'preview' : ''} ${isPreview && warning ? 'conflict' : ''}`}
                  style={{
                    left: `calc(${m.day * 20}% + 2px)`,
                    width: 'calc(20% - 4px)',
                    top: `calc(${((m.start - 540) / 540) * 100}% + 2px)`,
                    height: `calc(${((m.end - m.start) / 540) * 100}% - 4px)`,
                  }}
                  title={`${course.name} · ${days[m.day]} ${time(m.start)}–${time(m.end)} · ${course.room}`}
                >
                  <b>{course.name}</b>
                  <small>{course.room}</small>
                </div>
              )),
            )}
          </div>
        </div>
      </div>
      <div className={`preview-message ${warning ? 'warning' : ''}`} role="status">
        <Icon name={warning ? 'info' : 'cursor'} />
        <span>
          {preview
            ? `${preview.name} · ${warning ? '신청한 강의와 시간이 겹쳐요.' : '신청 전 미리보기'}`
            : '궁금한 강의에 커서를 올려보세요.'}
        </span>
      </div>
    </section>
  );
}
