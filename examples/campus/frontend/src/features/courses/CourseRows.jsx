import Icon from '../../shared/ui/Icon.jsx';
import { days, time } from './courses.js';
export default function CourseRows({ courses, state, busy, onPreview, onAction }) {
  return (
    <tbody id="course-rows">
      {courses.map((c) => {
        const enrolled = state.enrolledIds.includes(c.id),
          cart = state.cartIds.includes(c.id),
          full = c.enrolled >= c.capacity;
        return (
          <tr
            key={c.id}
            tabIndex={0}
            aria-label={`${c.name} 시간표 미리보기`}
            onMouseEnter={() => onPreview(c.id)}
            onMouseLeave={() => onPreview(null)}
            onFocus={() => onPreview(c.id)}
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) onPreview(null);
            }}
          >
            <td>
              <span className={`category-pill ${c.category.startsWith('교양') ? 'general' : ''}`}>
                {c.category}
              </span>
              <span className="course-code">{c.code}</span>
              <b className="course-name">{c.name}</b>
              <span className="course-meta">
                {c.professor}
                <span className="meta-divider">·</span>
                {c.department}
              </span>
            </td>
            <td>{c.credits}</td>
            <td>
              {c.meetings.map((m, i) => (
                <div key={i}>
                  {days[m.day]} {time(m.start)}–{time(m.end)}
                </div>
              ))}
              <small className="room">{c.room}</small>
            </td>
            <td>
              <div className="capacity">
                <b>{c.enrolled}</b> / {c.capacity}
              </div>
              <div className="seat-track">
                <i style={{ width: `${(c.enrolled / c.capacity) * 100}%` }} />
              </div>
            </td>
            <td>
              <div className="row-actions">
                {enrolled ? (
                  <button
                    className="cancel-button"
                    disabled={busy}
                    onClick={() => onAction('cancel', c)}
                  >
                    취소
                  </button>
                ) : (
                  <>
                    <button
                      className={`cart-button ${cart ? 'selected' : ''}`}
                      aria-label={`${c.name} ${cart ? '장바구니에서 빼기' : '장바구니 담기'}`}
                      disabled={busy}
                      onClick={() => onAction(cart ? 'removeCart' : 'cart', c)}
                    >
                      <Icon name="bag" />
                    </button>
                    <button
                      className="enroll-button"
                      disabled={full || busy}
                      onClick={() => onAction('enroll', c)}
                    >
                      {full ? '마감' : '신청'}
                    </button>
                  </>
                )}
              </div>
            </td>
          </tr>
        );
      })}
    </tbody>
  );
}
