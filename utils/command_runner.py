
import subprocess
import threading
import typing
import queue
import shlex

class CommandRunner:
    """
    Runs shell commands asynchronously in a background thread,
    emitting callbacks for output and completion.
    """

    def __init__(self):
        pass

    def run_command(
        self,
        command: typing.List[str],
        on_output: typing.Optional[typing.Callable[[str], None]] = None,
        on_complete: typing.Optional[typing.Callable[[int, str], None]] = None,
        on_error: typing.Optional[typing.Callable[[str], None]] = None,
        cwd: typing.Optional[str] = None
    ) -> threading.Thread:
        """
        Starts the command in a thread.

        Args:
            command: List of command arguments.
            on_output: Callback for stdout/stderr lines (real-time).
            on_complete: Callback when process finishes (return_code, full_output).
            on_error: Callback if an exception occurs starting the process.
            cwd: Working directory.

        Returns:
            The Thread object.
        """
        def target():
            try:
                # Use shlex.join for display/logging if needed, but subprocess takes list
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, # Merge stderr into stdout
                    text=True,
                    cwd=cwd,
                    bufsize=1, # Line buffered
                    encoding='utf-8',
                    errors='replace'
                )

                full_output = []

                # Read output line by line
                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            stripped_line = line.rstrip()
                            full_output.append(stripped_line)
                            if on_output:
                                on_output(stripped_line)

                process.wait()
                rc = process.returncode

                if on_complete:
                    on_complete(rc, "\n".join(full_output))

            except Exception as e:
                if on_error:
                    on_error(str(e))
                elif on_complete:
                     on_complete(-1, str(e))

        t = threading.Thread(target=target, daemon=True)
        t.start()
        return t

    def run_command_sync(self, command: typing.List[str]) -> typing.Tuple[int, str]:
        """Synchronous wrapper for simple checks."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return result.returncode, result.stdout + result.stderr
        except FileNotFoundError:
             return 127, "Command not found"
        except Exception as e:
             return -1, str(e)
