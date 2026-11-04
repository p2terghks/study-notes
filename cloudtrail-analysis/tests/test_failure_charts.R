source("failure_charts.R")
records <- data.frame(time = c("2026-01-01T09:00:00Z", "2026-01-02T09:10:00.100Z",
  "2026-01-02T10:00:00Z", NA, "bad-time"),
  result = c("Failure", "Failure", "Success", "Failure", "Failure"))
x <- failure_counts(records)
stopifnot(x$total == 4, x$invalid_time == 2, length(x$hourly) == 24,
  unname(x$hourly["09"]) == 2, sum(x$daily) == 2, sum(x$hourly) == 2,
  unname(x$daily["2026-01-01"]) == 1, unname(x$daily["2026-01-02"]) == 1)
for (input in list(records, records[FALSE, ], records[3, , drop = FALSE], records[4:5, ])) {
  f <- tempfile(fileext = ".png")
  save_failure_chart(input, f)
  stopifnot(file.exists(f), file.info(f)$size > 1000)
  signature <- readBin(f, "raw", n = 8)
  stopifnot(identical(signature, as.raw(c(137,80,78,71,13,10,26,10))))
  unlink(f)
}
# RStudio에서 오류가 났던 약 5.86 x 3.34인치 장치 크기로 회귀 검사합니다.
check_small_plot <- function(input) {
  f <- tempfile(fileext = ".png")
  png(f, width = 563, height = 321, res = 96)
  on.exit({ dev.off(); unlink(f) })
  counts <- plot_login_failures(input)
  stopifnot(identical(counts$total, failure_counts(input)$total))
}
for (input in list(records, records[FALSE, ], records[3, , drop = FALSE], records[4:5, ])) {
  check_small_plot(input)
}
cat("PASS: failure-only counts, UTC days/hours, invalid times, empty/no-failure PNGs, small-device plots\n")
