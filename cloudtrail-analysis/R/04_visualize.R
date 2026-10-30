# 시각화 (ggplot2). 차트 텍스트는 영어: PNG에 한글 폰트를 따로 설치하지 않아도 어디서든 동일하게 보이도록.
# 색 원칙: 심각도(순서형) = 한 색의 명도 램프, 2범주(성공/실패) = 검증된 파랑/주황 + 도형 병행.
source("R/00_config.R")

SEV_COLORS <- c(low = "#b9d4f1", medium = "#7fb0e8", high = "#2a78d6", critical = "#123e7c")
CAT_COLORS <- c(Success = "#2a78d6", Failure = "#eb6834")
INK <- "#0b0b0b"; INK2 <- "#52514e"; GRID <- "#e6e5e1"

theme_ct <- function() {
  theme_minimal(base_size = 11) +
    theme(
      text             = element_text(colour = INK),
      axis.text        = element_text(colour = INK2),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(colour = GRID, linewidth = 0.3),
      plot.title       = element_text(face = "bold", size = 13),
      plot.subtitle    = element_text(colour = INK2),
      plot.title.position = "plot",
      legend.position  = "top",
      legend.justification = "left"
    )
}

# 3) 규칙 x 시나리오 탐지 매트릭스 (칸 = 발동 건수, 색 = 해당 칸의 최고 심각도)
plot_detection_matrix <- function(findings, coverage) {
  cells <- findings |>
    group_by(id, rule_id) |>
    summarise(n = n(), sev = max(severity), .groups = "drop") |>
    mutate(sev = factor(as.character(sev), levels = names(SEV_COLORS)),
           lab_col = if_else(sev %in% c("high", "critical"), "white", INK))

  lvl_y <- rev(coverage$id)            # 라벨(기법 ID) 순서대로 위에서 아래로
  cells |>
    mutate(id = factor(id, levels = lvl_y)) |>
    ggplot(aes(rule_id, id)) +
    geom_tile(aes(fill = sev), colour = "white", linewidth = 0.8) +
    geom_text(aes(label = n, colour = lab_col), size = 3) +
    scale_colour_identity() +
    scale_fill_manual(values = SEV_COLORS, name = "highest severity", drop = FALSE) +
    scale_x_discrete(position = "top", drop = FALSE) +
    scale_y_discrete(drop = FALSE, limits = lvl_y) +
    labs(title = "Which rule fired on which scenario",
         subtitle = "cell = number of findings; blank = no finding; rows ordered by labeled MITRE technique",
         x = NULL, y = NULL) +
    theme_ct() + theme(panel.grid = element_blank(), axis.text.y = element_text(size = 8))
}

# 4) 로그인 시나리오 드릴다운: 출발지 IP별 성공/실패 타임라인
plot_login_timeline <- function(events) {
  d <- events |>
    filter(event_name == "ConsoleLogin", !is.na(login_result)) |>
    mutate(scenario_label = str_replace(id, "__", "\n"))
  ggplot(d, aes(event_time, source_ip, colour = login_result, shape = login_result)) +
    geom_point(size = 3, stroke = 0.9) +
    facet_wrap(~scenario_label, scales = "free", ncol = 2) +
    scale_x_datetime(date_labels = "%m-%d %H:%M", breaks = scales::breaks_pretty(4)) +
    scale_colour_manual(values = CAT_COLORS, name = NULL) +
    scale_shape_manual(values = c(Success = 16, Failure = 4), name = NULL) +
    labs(title = "Console logins by source IP", subtitle = "x marks failed logins", x = NULL, y = NULL) +
    theme_ct() + theme(strip.text = element_text(hjust = 0, size = 8, colour = INK2),
                       axis.text.x = element_text(size = 7), axis.text.y = element_text(size = 7))
}

save_all_figures <- function(events, findings, coverage, dir = DIR_FIG) {
  figs <- list(
    detection_matrix  = list(plot_detection_matrix(findings, coverage), 9, 7.5),
    login_timeline    = list(plot_login_timeline(events),              9, 6)
  )
  iwalk(figs, \(f, nm) ggsave(file.path(dir, paste0(nm, ".png")), f[[1]], width = f[[2]], height = f[[3]], dpi = 150, bg = "white"))
  invisible(names(figs))
}

if (sys.nframe() == 0) {
  events   <- readRDS(file.path(DIR_PROC, "events.rds"))
  findings <- readRDS(file.path(DIR_PROC, "findings.rds"))
  coverage <- read_csv(file.path(DIR_OUT, "coverage.csv"), show_col_types = FALSE)
  cat("저장:", paste(save_all_figures(events, findings, coverage), collapse = ", "), "\n")
}
