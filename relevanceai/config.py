import configparser
import os

from doc_utils.doc_utils import DocUtils

PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PATH, "config.ini")


class Config(DocUtils):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.read_config(CONFIG_PATH)
        super().__init__()

    def read_config(self, config_path):
        self.config.read(config_path)

    def view_options(self):
        return self.config._sections

    def get_option(self, option):
        return self.get_field(option, self.config)

    def set_option(self, option, value):
        self.set_field(option, self.config, str(value))

    def reset_to_default(self):
        self.read_config(CONFIG_PATH)

    @staticmethod
    def _create_default():
        config = configparser.ConfigParser()
        config["retries"] = {"number_of_retries": 1,
                             "seconds_between_retries": 2}
        config["logging"] = {"log_to_file": False, "logging_level": "ERROR",
                             'enable_logging': True, "log_file_name": "relevanceai"}
        config["upload"] = {"target_chunk_mb": 100}
        with open(CONFIG_PATH, "w") as configfile:
            config.write(configfile)


CONFIG = Config()

# To create the initial config
if __name__ == "__main__":
    Config._create_default()
