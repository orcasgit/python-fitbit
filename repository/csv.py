
from pathlib import Path
import pandas
from repository.local_storage import LocalStorage


class Csv(LocalStorage):
    def __init__(self) -> None:
        super().__init__("CSV")
        self.root = "./data_dumps/"

    def store(self, path, data):
        json = pandas.DataFrame.from_dict(data, orient="index")
        json.to_csv(self.root + path, encoding='utf-8', index=False)

    def store_profile(self, data):
        self.root += data["encodedId"] + "/"
        Path(self.root).mkdir(exist_ok=True)
        self.store("/profile.csv", data)
        return

    def store_activities(self, data, doc_name):
        return

    def store_intraday(self, data, date, doc_name):
        self.store("intraday_{0}_{1}.csv".format(date, doc_name), data)
        super()._log(doc_name)
        return

    def store_time_series(self, data, doc_name):
        self.store("time-series_{0}.csv".format(doc_name), data)
        super()._log(doc_name)
        return
