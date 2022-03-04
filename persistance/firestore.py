import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from persistance.local_storage import LocalStorage

class Firestore(LocalStorage):
    def __init__(self, certificate_path, collect_name) -> None:
        super().__init__("Firestore")
        cred = credentials.Certificate(certificate_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.collect_root = self.db.collection(collect_name)

    def store_profile(self, data):
        self.doc_profile = self.collect_root.document(data['encodedId'])
        self.doc_profile.set(data)
    
    def store_activities(self, data, doc_name):
        if hasattr(self, "collect_activities") == False:
            self.collect_activities = self.doc_profile.collection('activities')
            super()._log("activities")
        self.collect_activities.document(doc_name).set(data)
        super()._log(doc_name)

    def store_intraday(self, data, date, doc_name):
        if hasattr(self, "collect_intraday") == False:
            self.collect_intraday = self.doc_profile.collection('intraday')
            super()._log("intraday")
        current_date_document = self.collect_intraday.document(date.strftime('%Y-%m-%d'))
        current_date_document.collection("data").document(doc_name).set(data)
        super()._log(doc_name)

    def store_time_series(self, data, doc_name):
        if hasattr(self, "collect_time_series") == False:
            self.collect_time_series = self.doc_profile.collection('time_series')
            super()._log("time_series")
        self.collect_time_series.document(doc_name).set(data)
        super()._log(doc_name)

