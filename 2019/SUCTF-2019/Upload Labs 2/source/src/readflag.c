#include <stdio.h>

#define _GNU_SOURCE

void main() {
        seteuid(0);
        setegid(0);

        setuid(0);
        setgid(0);

        system("/bin/cat /flag");
}