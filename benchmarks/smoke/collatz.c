/* Smoke workload for gem5 SE feasibility: branchy integer loop, no I/O
 * beyond one line of stdout. Expected output: expected_stdout.txt, which is
 * generated independently by expected_output.py. */
#include <stdio.h>
#include <stdlib.h>

static unsigned long steps(unsigned long n) {
    unsigned long s = 0;
    while (n != 1) {
        n = (n & 1) ? 3 * n + 1 : n / 2;
        s++;
    }
    return s;
}

int main(int argc, char **argv) {
    unsigned long limit = argc > 1 ? strtoul(argv[1], NULL, 10) : 20000;
    unsigned long total = 0, best = 1, best_steps = 0;
    for (unsigned long i = 1; i <= limit; i++) {
        unsigned long s = steps(i);
        total += s;
        if (s > best_steps) { best_steps = s; best = i; }
    }
    printf("collatz limit=%lu total_steps=%lu longest=%lu steps=%lu\n",
           limit, total, best, best_steps);
    return 0;
}
