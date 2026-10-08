export const days = ['월', '화', '수', '목', '금'];
export const time = (minute) =>
  `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`;
export const chosen = (state) => state.courses.filter((c) => state.enrolledIds.includes(c.id));
export const credits = (state) => chosen(state).reduce((total, c) => total + c.credits, 0);
// 종료 시각과 다음 강의 시작 시각이 같으면 겹치지 않는다. 최종 검사는 서버에서 한다.
export const overlaps = (course, selected) =>
  selected.some(
    (other) =>
      other.id !== course.id &&
      other.meetings.some((a) =>
        course.meetings.some((b) => a.day === b.day && a.start < b.end && b.start < a.end),
      ),
  );
export function filterCourses(state, tab, filters) {
  const query = filters.search.trim().toLocaleLowerCase();
  return state.courses.filter(
    (c) =>
      (tab !== 'cart' || state.cartIds.includes(c.id)) &&
      (tab !== 'enrolled' || state.enrolledIds.includes(c.id)) &&
      (!query || `${c.name} ${c.professor} ${c.code}`.toLocaleLowerCase().includes(query)) &&
      (!filters.department || c.department === filters.department) &&
      (!filters.category || c.category === filters.category) &&
      (!filters.available ||
        (!state.enrolledIds.includes(c.id) &&
          c.enrolled < c.capacity &&
          !overlaps(c, chosen(state)) &&
          credits(state) + c.credits <= state.student.maxCredits)),
  );
}
