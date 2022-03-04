import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class FirestoreImpl():
    def __init__(self, certificate_path, collect_name) -> None:
        cred = credentials.Certificate(certificate_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.collect_root = self.db.collection(collect_name)

    def _log(self, name):
        print("  > " + name + " stored.")

    def store_profile(self, data):
        self.user_id = data['encodedId']
        self.doc_profile = self.collect_root.document(self.user_id)
        result = self.doc_profile.set(data)
    
    def store_activities(self, data, doc_name):
        if hasattr(self, "collect_activities") == False:
            self.collect_activities = self.doc_profile.collection('activities')
            self._log("activities")
        result = self.collect_activities.document(doc_name).set(data)
        self._log(doc_name)

    def store_intraday(self, data, doc_name):
        if hasattr(self, "collect_intraday") == False:
            self.collect_intraday = self.doc_profile.collection('intraday')
            self._log("intraday")
        result = self.collect_intraday.document(doc_name).set(data)
        self._log(doc_name)

    def store_time_series(self, data, doc_name):
        if hasattr(self, "collect_time_series") == False:
            self.collect_time_series = self.doc_profile.collection('time_series')
            self._log("time_series")
        self.collect_time_series.document(doc_name).set(data)
        self._log(doc_name)

