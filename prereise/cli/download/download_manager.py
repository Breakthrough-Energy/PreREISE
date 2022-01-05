import argparse

from prereise.cli.data_sources import get_data_sources_list
from prereise.cli.helpers import add_data_source_to_download_parser


def generate_parser():
    """Creates main command line interface parser

    :return: (*argparse.ArgumentParser*)
    """
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()
    for data_source in get_data_sources_list():
        add_data_source_to_download_parser(data_source, subparser)
    return parser


def main():
    """Main function that initializes parser and calls parser
    with arguments the user passed in via command line interface
    """
    parser = generate_parser()
    args = parser.parse_args()
    args.func(**args.__dict__)


if __name__ == "__main__":
    main()
