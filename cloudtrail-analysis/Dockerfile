# 주의: 이 Dockerfile은 작성만 했고 실행해 보지 않았습니다 (이 환경에서는 docker를 쓸 수 없었음).
FROM rocker/r-ver:4.3.3

RUN apt-get update \
 && apt-get install -y --no-install-recommends pandoc libcurl4-openssl-dev libssl-dev libxml2-dev \
 && rm -rf /var/lib/apt/lists/*

RUN R -q -e 'install.packages(c("tidyverse", "jsonlite", "rmarkdown"))'

WORKDIR /app
COPY R/ R/
COPY report.Rmd run_pipeline.R ./

ENV LANG=en_US.UTF-8
CMD ["Rscript", "run_pipeline.R"]
