# 실패 기록을 UTC 날짜별·시각대별로 집계합니다. 중복 기록은 그대로 셉니다.
failure_counts <- function(records) {
  failed <- records[!is.na(records$result) & records$result == "Failure", , drop = FALSE]
  times <- as.POSIXct(failed$time, format = "%Y-%m-%dT%H:%M:%OSZ", tz = "UTC")
  valid <- times[!is.na(times)]
  daily <- table(format(valid, "%Y-%m-%d", tz = "UTC"))
  hourly <- table(factor(format(valid, "%H", tz = "UTC"), levels = sprintf("%02d", 0:23)))
  list(total = nrow(failed), invalid_time = sum(is.na(times)), daily = daily, hourly = hourly)
}

# RStudio에서는 plot_login_failures(records)로 Plots 창에 그릴 수 있습니다.
plot_login_failures <- function(records) {
  counts <- failure_counts(records)
  previous <- par(no.readonly = TRUE)
  on.exit(par(previous))
  par(mfrow = c(2, 1))
  # 작은 RStudio Plots 창에서도 여백이 그릴 영역을 넘지 않게 합니다.
  compact <- dev.size("in")[[2]] < 5
  par(mar = c(4, 4, 3, 1), oma = c(1, 0, 3, 0),
      mex = if (compact) 0.45 else 1, cex = if (compact) 0.7 else 1)
  if (length(counts$daily)) {
    positions <- barplot(counts$daily, col = "#d97745", border = NA,
      main = "Failed logins by date (UTC)", ylab = "Failure records",
      cex.names = 0.8, ylim = c(0, max(counts$daily) * 1.18))
    text(positions, counts$daily, labels = counts$daily, pos = 3, cex = 0.8)
  } else {
    plot.new()
    title("Failed logins by date (UTC)")
    text(0.5, 0.5, "No failed logins with a valid time")
  }
  barplot(counts$hourly, col = "#477fbb", border = NA,
    main = "Failed logins by hour of day (UTC, all dates)",
    xlab = "Hour (00-23 UTC)", ylab = "Failure records", cex.names = 0.8,
    ylim = c(0, max(1, counts$hourly) * 1.18))
  mtext(sprintf("Failed login records: %d | Missing/invalid time: %d", counts$total,
    counts$invalid_time), outer = TRUE, side = 3, line = 1, font = 2)
  mtext("Repeated source events are counted; missing/invalid times are omitted from bars.",
    outer = TRUE, side = 1, cex = 0.75)
  invisible(counts)
}

save_failure_chart <- function(records, path = "output/login_failures.png") {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  png(path, width = 1400, height = 1000, res = 140, bg = "white")
  on.exit(dev.off())
  plot_login_failures(records)
  invisible(path)
}
