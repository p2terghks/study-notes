#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 성공하면 1, 입력이 끝났으면 0을 반환합니다.
static int read_score(size_t index, int *result) {
    char line[128];
    for (;;) {
        printf("Score %zu: ", index);
        fflush(stdout);
        if (fgets(line, sizeof line, stdin) == NULL) {
            return 0;
        }
        // 버퍼보다 긴 줄은 남은 내용까지 버리고 다시 입력받습니다.
        if (strchr(line, '\n') == NULL && !feof(stdin)) {
            int ch;
            while ((ch = getchar()) != '\n' && ch != EOF) {
            }
            puts("Input is too long.");
            continue;
        }
        char *end = NULL;
        errno = 0;
        long value = strtol(line, &end, 10);
        int has_number = end != line;
        while (isspace((unsigned char)*end)) {
            ++end;
        }
        if (!has_number || errno == ERANGE || *end != '\0'
                || value < 0 || value > 100) {
            puts("Enter an integer from 0 to 100.");
            continue;
        }
        *result = (int)value;
        return 1;
    }
}

int main(void) {
    int scores[3] = {0};
    size_t count = sizeof scores / sizeof scores[0];
    int total = 0;
    int passed = 0;
    for (size_t i = 0; i < count; ++i) {
        if (!read_score(i + 1, &scores[i])) {
            fputs("Input ended before all scores were entered.\n", stderr);
            return 1;
        }
        total += scores[i];
        if (scores[i] >= 60) {
            ++passed;
        }
    }
    printf("Average: %.2f\n", (double)total / count);
    printf("Passed: %d\n", passed);
    return 0;
}
