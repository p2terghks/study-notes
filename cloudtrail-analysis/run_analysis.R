# 프로젝트 폴더에서 실행: Rscript run_analysis.R 로그.json [출력폴더]
source("login_records.R")
source("failure_charts.R")
args <- commandArgs(trailingOnly = TRUE)
if (!length(args)) stop("사용법: Rscript run_analysis.R 로그.json [출력폴더]")
output_dir <- if (length(args) >= 2) args[[2]] else "output"
records <- login_records(read_events(args[[1]]))
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
write.csv(records, file.path(output_dir, "login_records.csv"), row.names = FALSE,
  na = "", fileEncoding = "UTF-8")
save_failure_chart(records, file.path(output_dir, "login_failures.png"))
print(records, row.names = FALSE)
cat(sprintf("로그인 %d건 / 실패 %d건 / 저장 위치: %s\n", nrow(records),
  sum(records$result == "Failure", na.rm = TRUE), output_dir))
