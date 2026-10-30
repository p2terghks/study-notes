# 전체 파이프라인 실행: Rscript run_pipeline.R  (프로젝트 루트에서 실행)
#   1) 데이터 다운로드  2) 파싱  3) 탐지 + 채점  4) 차트 저장  5) HTML 리포트 렌더링
source("R/00_config.R")
source("R/01_download.R")
source("R/02_parse.R")
source("R/03_detect.R")
source("R/04_visualize.R")

message("[1/5] 데이터 다운로드")
res <- download_all(manifest)
print(count(res, status))
if (any(!res$status %in% c("cached", "downloaded"))) stop("일부 데이터셋을 받지 못했습니다. 위 표를 확인하세요.")

message("[2/5] 파싱")
events <- load_all_events(manifest)
saveRDS(events, file.path(DIR_PROC, "events.rds"))
write_csv(events, file.path(DIR_PROC, "events.csv"))

message("[3/5] 탐지 규칙 실행 및 채점")
findings <- run_detections(events, rules)
coverage <- evaluate_coverage(findings, events, rules)
saveRDS(findings, file.path(DIR_PROC, "findings.rds"))
write_csv(findings, file.path(DIR_OUT, "findings.csv"))
write_csv(coverage, file.path(DIR_OUT, "coverage.csv"))
cat(sprintf("  이벤트 %d건 / 탐지 %d건 / 라벨 일치 %d of %d 시나리오\n",
            nrow(events), nrow(findings), sum(coverage$detected), nrow(coverage)))

message("[4/5] 차트 저장")
save_all_figures(events, findings, coverage)

message("[5/5] 리포트 렌더링")
rmarkdown::render("report.Rmd", output_dir = DIR_OUT, quiet = TRUE)
message("완료: ", file.path(DIR_OUT, "report.html"))
