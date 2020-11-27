import re
import os
import configparser
from argparse import Namespace, ArgumentParser

import chardet

parser = ArgumentParser(description="Merge contents of folder into one output file")
parser.add_argument(
    "--output",
    type=str,
    help='Output file location ("codingame.volatile.py" be ' "default)",
)
parser.add_argument(
    "--workdir",
    type=str,
    help="Folder that will be searched for files to merge in output file",
)
parser.add_argument(
    "--order",
    type=str,
    help="Forcing the order of files copied from the workdir (use comma-separated "
    "file names)",
)
parser.add_argument(
    "--header",
    type=str,
    help="File from which the top part of output file will be copied (you should put "
    "all of the imports/using/includes here depending on your language)",
)
parser.add_argument(
    "--footer",
    type=str,
    help="File from which the bottom part of output file will be copied",
)
parser.add_argument(
    "--comment", type=str, help='Comment character ("#" by default)',
)
parser.add_argument(
    "--separator-start",
    type=str,
    help="Character appended to comment "
    'indicating start of file contents ("-" by '
    "default)",
)
parser.add_argument(
    "--separator-end",
    type=str,
    help="Character appended to comment "
    'indicating end of file contents ("=" by '
    "default)",
)
parser.add_argument(
    "--separator-length",
    type=str,
    help="how many characters to left-pad to indicate contents from other files (80 "
    "by default)",
)
parser.add_argument(
    "--file-regex",
    type=str,
    help="pythonic regex used to filter-out files in "
    'workdir (".*" by default - it will process all of the files in the workdir '
    "folder)",
)
parser.add_argument(
    "--exclude-line-regex",
    type=str,
    help="pythonic regex used to filter-out lines of files that would cause a mess "
    'during the merge ("^from codingame\.|^import codingame|^from \.|^import \." by '
    "default to exclude python local imports)",
)
parser.add_argument("--debug", action="store_true", help="print current settings")
parser.add_argument(
    "--write",
    action="store_true",
    help="Write current settings in form of a file ("
    "they will be used instead of the command "
    "line settings)",
)

config = configparser.ConfigParser(
    defaults={
        "output": "codingame.volatile.py",
        "workdir": "codingame/",
        "file_regex": ".*",
        "exclude_line_regex": "^from codingame\.|^import codingame|^from \.|^import \.",
        "comment": "#",
        "separator_start": "-",
        "separator_end": "=",
        "separator_length": "80",
    },
    default_section="merger",
)


def check_file_exists(file_path):
    if not os.path.exists(file_path):
        parser.error(f'No "{file_path}" file present in {os.getcwd()}')


def check_workdir_exists():
    if not os.path.isdir(config["merger"]["workdir"]):
        parser.error(
            f"No \"{config['merger']['workdir']}\" directory present in {os.getcwd()}"
        )


def write_to_output_file(
    file_name,
    output_file,
    exclude_line_regex,
    disable_headers=False,
    ignore_regex=False,
):
    bytes = min(32, os.path.getsize(file_name))
    with open(file_name, "rb") as byte_file:
        raw = byte_file.read(bytes)
        encoding = chardet.detect(raw)["encoding"]

    with open(file_name, "r", encoding=encoding) as current_file:
        if not disable_headers:
            start_file_comment = f'{config["merger"]["comment"]} file "{file_name}" '.ljust(
                int(config["merger"]["separator_length"]),
                config["merger"]["separator_start"][0],
            )
            output_file.write(f"\n{start_file_comment}\n")
        for line in current_file.readlines():
            if ignore_regex or not exclude_line_regex.search(line):
                output_file.write(line)
        if not disable_headers:
            end_file_comment = (
                f'{config["merger"]["comment"]} end of file "{file_name}" '
                f"".ljust(
                    int(config["merger"]["separator_length"]),
                    config["merger"]["separator_end"][0],
                )
            )
            output_file.write(f"\n\n\n{end_file_comment}\n")


def log_values():
    print("")
    print("output: ", config["merger"].get("output", "none"))
    print("workdir: ", config["merger"].get("workdir", "none"))
    print("order: ", config["merger"].get("order", "none"))
    print("file_regex: ", config["merger"].get("file_regex", "none"))
    print("exclude_line_regex: ", config["merger"].get("exclude_line_regex", "none"))
    print("header: ", config["merger"].get("header", "none"))
    print("footer: ", config["merger"].get("footer", "none"))
    print("comment: ", config["merger"].get("comment", "none"))
    print("separator_start: ", config["merger"].get("separator_start", "none"))
    print("separator_end: ", config["merger"].get("separator_end", "none"))
    print("separator_length: ", config["merger"].get("separator_length", "none"))
    print("")


def copy_parser_arguments_to_config(arguments: Namespace):
    if arguments.file_regex is not None:
        config["merger"]["file_regex"] = arguments.file_regex
    if arguments.exclude_line_regex is not None:
        config["merger"]["exclude_line_regex"] = arguments.exclude_line_regex
    if arguments.output is not None:
        config["merger"]["output"] = arguments.output
    if arguments.workdir is not None:
        config["merger"]["workdir"] = arguments.workdir
    if arguments.header is not None:
        config["merger"]["header"] = arguments.header
    if arguments.footer is not None:
        config["merger"]["footer"] = arguments.header
    if arguments.comment is not None:
        config["merger"]["comment"] = arguments.comment
    if arguments.order is not None:
        config["merger"]["order"] = arguments.order


def get_parameters_from_config():
    order = None
    output_file_location = config["merger"]["output"]
    work_dir = config["merger"]["workdir"]
    file_regex = re.compile(config["merger"]["file_regex"])
    exclude_line_regex = re.compile(config["merger"]["exclude_line_regex"])
    header_file = None
    footer_file = None

    if "header" in config["merger"]:
        header_file = config["merger"]["header"]

    if "footer" in config["merger"]:
        footer_file = config["merger"]["footer"]

    if "order" in config["merger"]:
        order = config["merger"]["order"].split(",")

    check_file_exists(output_file_location)
    check_workdir_exists()

    if order is not None:
        for file_name in order:
            check_file_exists(os.path.join(work_dir, file_name))

    if header_file is not None:
        check_file_exists(os.path.join(work_dir, header_file))

    if footer_file is not None:
        check_file_exists(os.path.join(work_dir, footer_file))

    files_to_watch = [
        f for f in os.listdir(work_dir) if os.path.isfile(os.path.join(work_dir, f))
    ]

    return (
        order,
        output_file_location,
        work_dir,
        file_regex,
        exclude_line_regex,
        header_file,
        footer_file,
        files_to_watch,
    )


def main():
    arguments = parser.parse_args()
    if os.path.exists("cgmerger.conf"):
        config.read("cgmerger.conf")
    else:
        print("")
        print(
            "No cgmerger.conf file found. The script will run with default "
            "settings. run the command with --write flag to write new cgmerger.conf "
            "file or override the current one. Run the command with --debug flag to "
            "check the current settings"
        )
        print("")

    copy_parser_arguments_to_config(arguments)

    if arguments.debug:
        log_values()
        parser.exit(message="No further operations will be performed")

    if arguments.write:
        with open("cgmerger.conf", "w") as config_file:
            config.write(config_file)
        log_values()
        parser.exit(message="Config file created with listed values")

    (
        order,
        output_file_location,
        work_dir,
        file_regex,
        exclude_line_regex,
        header_file,
        footer_file,
        files_to_watch,
    ) = get_parameters_from_config()

    with open(output_file_location, "w") as output_file:
        # all of the files, which are not in order
        if header_file is not None:
            write_to_output_file(
                os.path.join(work_dir, header_file),
                output_file,
                exclude_line_regex,
                disable_headers=True,
                ignore_regex=True,
            )

        # now files that should go in order
        if order is not None:
            for f in order:

                if f == header_file:
                    continue

                if f == footer_file:
                    continue

                write_to_output_file(
                    os.path.join(work_dir, f), output_file, exclude_line_regex
                )

        for f in files_to_watch:
            if order is not None and f in order:
                continue

            if f == header_file:
                continue

            if f == footer_file:
                continue

            if not file_regex.search(f):
                continue

            write_to_output_file(
                os.path.join(work_dir, f), output_file, exclude_line_regex
            )

        if footer_file is not None:
            write_to_output_file(
                os.path.join(work_dir, footer_file),
                output_file,
                exclude_line_regex,
                disable_headers=True,
            )