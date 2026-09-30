#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n, q;
    if (scanf("%d %d", &n, &q) != 2) return 1;
    long long *prefix = calloc((size_t)n + 1, sizeof *prefix);
    if (prefix == NULL) return 1;
    for (int i = 1; i <= n; ++i) {
        long long value;
        if (scanf("%lld", &value) != 1) { free(prefix); return 1; }
        prefix[i] = prefix[i - 1] + value;
    }
    for (int i = 0; i < q; ++i) {
        int left, right;
        if (scanf("%d %d", &left, &right) != 2) { free(prefix); return 1; }
        printf("%lld\n", prefix[right] - prefix[left - 1]);
    }
    free(prefix);
    return 0;
}
