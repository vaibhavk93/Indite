/*
 * indite's app executable (Contents/MacOS/indite). It starts Contents/Resources/run.sh as a CHILD and stays
 * running until it ends.
 *
 * Why not just a shell script that execs Python: macOS then judged the Accessibility permission against the
 * Python program itself, which has no permission of its own, so "key access" stayed off even with indite switched
 * on (15 Oct). A parent that stays alive is the "responsible process": macOS credits everything its children do -
 * the hotkey, typing, the microphone, screen recording - to indite, the app the person actually allowed.
 */
#include <libgen.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;
static pid_t child = 0;

static void pass_on(int sig) {
    if (child > 0) kill(child, sig);
}

int main(void) {
    char exe[PATH_MAX], real[PATH_MAX], script[PATH_MAX];
    uint32_t size = sizeof exe;
    if (_NSGetExecutablePath(exe, &size) != 0 || !realpath(exe, real)) return 1;
    snprintf(script, sizeof script, "%s/../Resources/run.sh", dirname(real));

    signal(SIGTERM, pass_on);
    signal(SIGINT, pass_on);
    signal(SIGHUP, pass_on);

    char *argv[] = {"/bin/bash", script, NULL};
    if (posix_spawn(&child, "/bin/bash", NULL, NULL, argv, environ) != 0) return 1;

    int status = 0;
    while (waitpid(child, &status, 0) < 0) {
        /* interrupted by a signal we passed on: keep waiting for the child to finish */
    }
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
