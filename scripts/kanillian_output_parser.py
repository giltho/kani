import argparse
from pathlib import Path
import json
import sys
from colorama import Fore, Style

# STATUS CODES:
# 0b00000 = 0 : Success
# 0b00001 = 1: Python Error
# 0b00010 = 2 : Ended in Assert error or execution failure
# 0b00100 = 4 : Ended because of unhandled assert
# 0b01000 = 8: Ended with unknown status
# Any combination of the 3 aboves means that several of those happened
# 0b10000 = 16 : Something else happened


exec_stats = {
    "successes": 0,
    "verification_failures": 0,
    "unhandled_failures": {},
    "unknown": 0,
    "gillian_failures": 0,
}

stats_file = {
    "file": None
}

class Status:
    SUCCESS = 0b00000
    PYTHON_ERROR = 0b00001
    ASSERT_ERROR = 0b00010
    UNHANDLED_GOTO = 0b00100
    ENDED_UNKNOWN = 0b01000
    SOMETHING_ELSE = 0b10000

    _status = PYTHON_ERROR

    def success(self):
        self._status = Status.SUCCESS
        return self

    def assert_error(self):
        self._status |= Status.ASSERT_ERROR
        return self

    def unhandled_goto(self):
        self._status |= Status.UNHANDLED_GOTO
        return self

    def ended_unknown(self):
        self._status |= Status.ENDED_UNKNOWN
        return self

    def something_else(self):
        self._status = Status.SOMETHING_ELSE
        return self

    def exit(self):

        with open(stats_file["file"], 'w') as f:
            json.dump(exec_stats, f)
        exit(self._status)


class Result:
    SUCCESS = "Success"
    ASSERT_FAILED = "AssertFailed"
    UNHANDLED_AT_EXEC = "UnhandledAtExec"
    UNKNOWN = "Unknown"

    def __init__(self, reason, feature=None):
        self.reason = reason
        self.feature = feature

    def is_unhandled(self):
        return self.reason == Result.UNHANDLED_AT_EXEC

    def is_success(self):
        return self.reason == Result.SUCCESS

    def is_assert_failed(self):
        return self.reason == Result.ASSERT_FAILED

    def is_unknown(self):
        return self.reason == Result.UNKNOWN

    def success():
        return Result(Result.SUCCESS)

    def assert_failed():
        return Result(Result.ASSERT_FAILED)

    def unhandled(feature):
        return Result(Result.UNHANDLED_AT_EXEC, feature)

    def unknown():
        return Result(Result.UNKNOWN)

def colored_text(color, text):
    """
    Only use colored text if running in a terminal to avoid dumping escape
    characters
    """
    if sys.stdout.isatty():
        return color + text + Style.RESET_ALL
    else:
        return text

def one_wpst_status(json):
    if json[0] == "RSucc":
        exec_stats["successes"] += 1
        return Result.success()
    if json[0] == "RFail":
        first_error = json[1]["errors"][0]
        if first_error[0] == "EState":
            exec_stats["verification_failures"] += 1
            return Result.assert_failed()
        elif first_error[0] == "EFailReached":
            fail_code = first_error[1]["fail_code"]
            if fail_code == "unhandled":
                feature = first_error[1]["fail_params"][0][1][1]
                if feature in exec_stats["unhandled_failures"]:
                    exec_stats["unhandled_failures"][feature] += 1
                else:
                    exec_stats["unhandled_failures"][feature] = 1
                return Result.unhandled(feature)
            else:
                exec_stats["verification_failures"] += 1
                return Result.assert_failed()
        else:
            exec_stats["unknown"] += 1
            return Result.unknown()
    exec_stats["unknown"] += 1
    return Result.unknown()


parser = argparse.ArgumentParser(description='Parse the result of a Kanillian run')
parser.add_argument('file', metavar="FILE", type=Path,
                    help='File that contains the stdout of the Kanillian run')
parser.add_argument('harness', metavar='HARNESS', type=str, help='Pretty name for the harness')
parser.add_argument('--stats', metavar="STATS_FILE", type=Path, help='File to write the exec stats in')
args = parser.parse_args()

stats_file["file"] = args.stats

with open(args.file, 'r') as f:
    content = f.read()

HARNESS = "Harness: "
INDENT = " " * (len(HARNESS) - 2) + "- "

print(f"{HARNESS}{args.harness}")

# Otherwise, check for the results in JSON form, and report that
start_string = '===JSON RESULTS===\n'
start_string_index = content.find(start_string)
if start_string_index != -1:
    status = Status().success()
    start_index = content.find(start_string) + len(start_string)

    values = json.loads(content[start_index:])

    results = [one_wpst_status(i) for i in values]

    non_success = [x for x in results if not x.is_success()]
    if non_success == []:
        print(f'{INDENT}Status: {colored_text(Fore.GREEN, "SUCCESS")}\n')
    else:
        print(f'{INDENT}Status: {colored_text(Fore.RED, "ERROR")}')
        failed = len([x for x in results if x.is_assert_failed()])
        if failed > 0:
            status.assert_error()
            print(f'{INDENT}Execution failures: {failed}')

        unhandled = set([x.feature for x in non_success if x.is_unhandled()])
        if len(unhandled) > 0:
            status.unhandled_goto()
            print(f'{INDENT}Failures because of unhandled features: {len(unhandled)}')
            print(f'{INDENT}Unhandled features: {", ".join(unhandled)}')

        unknown = len([x for x in results if x.is_unknown()])
        if unknown > 0:
            status.ended_unknown()
            print(f'{colored_text(Fore.YELLOW, "Unknown cases:")} {unknown}')
    status.exit()


print(f'{colored_text(Fore.RED, "GILLIAN FAILURE")}')
exec_stats["gillian_failures"] += 1
Status().something_else().exit()
