scores <- c(55, 80, NA, 95, 70)
valid <- scores[!is.na(scores)]
stopifnot(length(valid) > 0)
cat("인원:", length(valid), "\n")
cat("평균:", mean(valid), "\n")
cat("합격:", sum(valid >= 60), "\n")
cat("정렬:", sort(valid), "\n")
