from dataclasses import dataclass


@dataclass
class GribRecordInfo:
    """Class to hold metadata on a GRIB record. GRIB (General Regularly-distributed
    Information in Binary) is a concise data format commonly used in meteorology to
    store historical and forecast weather data. GRIB files can have corresponding
    index files that holds metadata about the data inside GRIB files. More info
    on index files can be found at
    `this link <https://github.com/blaylockbk/Herbie/blob/18945e4c5103386c98d08dcb2de590e2ac14c3d5/docs/user_guide/grib2.rst#how-grib-subsetting-works-in-herbie>`_

    :param str message_number: message number of the GRIB record
    :param str beginning_byte: byte that the GRIB record starts at
    :param str ending_byte: byte that the GRIB record ends at. If None
        then ending_byte is the end of file
    :param str initialization_date: date and hour that the data is for
    :param str variable: string designating what kind of data
    :param str level: additional string that designates more information about
        type of data
    :param str forecast: designates how many hours into the future
        this data is forecasted for
    """

    message_number: str
    beginning_byte: str
    ending_byte: str
    initialization_date: str
    variable: str
    level: str
    forecast: str

    @classmethod
    def from_string(cls, raw_string, next_raw_string=None):
        """Creates a GribRecordInfo object from a specific string.
        Information on the string format can be found at
        `this link <https://github.com/blaylockbk/Herbie/blob/18945e4c5103386c98d08dcb2de590e2ac14c3d5/docs/user_guide/grib2.rst#how-grib-subsetting-works-in-herbie>`_

        :param str raw_string: a record line following the format
            MESSAGE_NUMBER:BEGINNING_BYTE:INITIALIZATION_DATE:VARIABLE:LEVEL:FORECAST
        :param str next_raw_string: the following record line. This
            is needed to know when the next record starts, so we know where
            the current record ends.

        :return: (*GribRecordInfo*)
        """
        details = raw_string.split(":")
        assert len(details) >= 6
        ending_byte = None
        if next_raw_string:
            ending_byte = str(int(next_raw_string.split(":")[1]) - 1)
        return cls(
            message_number=details[0],
            beginning_byte=details[1],
            ending_byte=ending_byte,
            initialization_date=details[2],
            variable=details[3],
            level=details[4],
            forecast=details[5],
        )

    @classmethod
    def generate_grib_record_information_list(
        cls, raw_record_information_list, index_list
    ):
        """Creates a list of GribRecordInfo objects from a
        list of raw strings and a list of integers that designate
        which raw strings to use to create GribRecordInfo objects.

        :param list raw_record_information_list: a list of record lines that
            follow the format:
            MESSAGE_NUMBER:BEGINNING_BYTE:INITIALIZATION_DATE:VARIABLE:LEVEL:FORECAST
        :param list index_list: a list of integers representing indices
            to index into raw_record_information_list to create
            GribRecordInfo objects out of

        :return: (*list*) -- a list of GribRecordInfo objects
        """
        duplicate_list = raw_record_information_list[:]
        duplicate_list.append(None)
        return [
            cls.from_string(duplicate_list[ind], duplicate_list[ind + 1])
            for ind in index_list
        ]

    def byte_range_header_string(self):
        """Returns a string providing the range of
        the byte that the record starts at to the byte that the record
        ends at.

        :return: (*str*)
        """
        return (
            f"{self.beginning_byte}-{self.ending_byte}"
            if self.ending_byte
            else f"{self.beginning_byte}-"
        )

    @classmethod
    def full_file(cls):
        """Creates a GribRecordInfo that represents a whole file

        :return: (*GribRecordInfo*) -- a GribRecordInfo representing a whole file
        """
        return cls(0, 0, None, None, None, None, None)
