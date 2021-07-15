from prereise.cli.data_sources.data_source import NotSupportedDataSource


class DemandData(NotSupportedDataSource):
    @property
    def command_name(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_name`

        :return: (*str*) -- command name
        """
        return "demand_data"
