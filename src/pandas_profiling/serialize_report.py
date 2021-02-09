import warnings
from pathlib import Path
from typing import Union

from pandas_profiling.config import Config, config
from pandas_profiling.report.presentation.core import Root
from pandas_profiling.version import __version__


class SerializeReport:
    """Extend the report to be able to dump and load reports."""

    df_hash = None
    df = None
    _df_hash = None
    _report = None
    _description_set = None
    _title = None

    def dumps(self) -> bytes:
        """
        Serialize ProfileReport and return bytes for reproducing ProfileReport or Caching.

        Returns:
            Bytes which contains hash of DataFrame, config, _description_set and _report
        """
        # import pickle
        import dill as pickle

        # Note: _description_set and _report may are None if they haven't been computed
        return pickle.dumps(
            [self.df_hash, config, self._description_set, self._report, self._title]
        )

    def loads(self, data: bytes, ignore_config: bool = False):
        """
        Deserialize the serialized report

        Args:
            data: The bytes of a serialize ProfileReport object.
            ignore_config: If set to True, the ProfileReport config will be overwritten with the current global Config.
                           If set to False, the function checks if the configs match

        Raises:
            ValueError: if ignore_config is set to False and the configs do not match.

        Returns:
            self
        """
        # import pickle
        import dill as pickle

        try:
            (
                df_hash,
                loaded_config,
                loaded_description_set,
                loaded_report,
                loaded_title,
            ) = pickle.loads(data)
        except Exception as e:
            raise ValueError(f"Failed to load data: {e}")

        if not all(
            (
                df_hash is None or isinstance(df_hash, str),
                loaded_title is None or isinstance(loaded_title, str),
                isinstance(loaded_config, Config),
                loaded_description_set is None
                or isinstance(loaded_description_set, dict),
                loaded_report is None or isinstance(loaded_report, Root),
            )
        ):
            raise ValueError(
                f"Failed to load data: file may be damaged or from an incompatible version"
            )
        if (df_hash == self.df_hash) or (
            config.is_default and self.df is None
        ):  # load to an empty ProfileReport
            # Set description_set, report, sample if they are None，or raise an warning.
            if self._description_set is None:
                self._description_set = loaded_description_set
            else:
                warnings.warn(
                    f"The description set of current ProfileReport is not None. It won't be loaded."
                )
            if self._report is None:
                self._report = loaded_report
            else:
                warnings.warn(
                    f"The report of current ProfileReport is not None. It won't be loaded."
                )

            # overwrite config
            config.update(loaded_config)

            # warn if version not equal
            if (
                loaded_description_set is not None
                and loaded_description_set["package"]["pandas_profiling_version"]
                != __version__
            ):
                warnings.warn(
                    f"The package version specified in the loaded data is not equal to the version installed. "
                    f"Currently running on pandas-profiling {__version__} , while loaded data is generated by pandas_profiling, {loaded_description_set['package']['pandas_profiling_version']}."
                )

            # set df_hash and title
            self._df_hash = df_hash
            self._title = loaded_title

        else:
            raise ValueError("DataFrame does not match with the current ProfileReport.")
        return self

    def dump(self, output_file: Union[Path, str]):
        """
        Dump ProfileReport to file
        """
        if not isinstance(output_file, Path):
            output_file = Path(str(output_file))

        output_file = output_file.with_suffix(".pp")
        output_file.write_bytes(self.dumps())

    def load(self, load_file: Union[Path, str], ignore_config: bool = False):
        """
        Load ProfileReport from file

        Raises:
             ValueError: if the DataFrame or Config do not match with the current ProfileReport
        """
        if not isinstance(load_file, Path):
            load_file = Path(str(load_file))

        self.loads(load_file.read_bytes(), ignore_config=ignore_config)
        return self
