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
        print(name + " stored.")

    def store_profile(self, data):
        self.user_id = data['encodedId']
        self.doc_profile = self.collect_root.document(self.user_id)
        result = self.doc_profile.set(data)
        self._log("profile")
    
    def store_activities(self, data, doc_name):
        if hasattr(self, "collect_activities") == False:
            self.collect_activities = self.doc_profile.collection('activities')
            print("activities collection created.")
        result = self.collect_activities.document(doc_name).set(data)
        self._log(doc_name)

    def store_intraday(self, data, doc_name):
        if hasattr(self, "collect_intraday") == False:
            self.collect_intraday = self.doc_profile.collection('intraday')
            print("intraday collection created.")
        result = self.collect_intraday.document(doc_name).set(data)
        self._log(doc_name)
