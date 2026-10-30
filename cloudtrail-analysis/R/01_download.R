# 공개 데이터셋 다운로드 (이미 받은 파일은 건너뜀)
source("R/00_config.R")

download_all <- function(manifest, force = FALSE) {
  results <- pmap_chr(manifest, function(id, url, raw_path, ...) {
    if (file.exists(raw_path) && !force) return("cached")
    dir.create(dirname(raw_path), recursive = TRUE, showWarnings = FALSE)
    status <- tryCatch({
      download.file(url, raw_path, mode = "wb", quiet = TRUE)
      # LFS 포인터 파일("version https://git-lfs...")이 내려온 경우를 걸러낸다
      head1 <- readLines(raw_path, n = 1, warn = FALSE)
      if (length(head1) && grepl("^version https://git-lfs", head1)) {
        unlink(raw_path)
        "lfs-pointer (실제 데이터 아님)"
      } else "downloaded"
    }, error = function(e) paste("error:", conditionMessage(e)))
    status
  })
  tibble(id = manifest$id, status = results)
}

if (sys.nframe() == 0) {
  res <- download_all(manifest)
  print(count(res, status))
  failed <- filter(res, !status %in% c("cached", "downloaded"))
  if (nrow(failed)) { print(failed); quit(status = 1) }
}
