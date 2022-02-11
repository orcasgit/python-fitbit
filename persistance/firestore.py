import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class FirestoreImpl():
    def __init__(self, certificate_path, collect_name, user_id) -> None:
        cred = credentials.Certificate(certificate_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.collect_root = self.db.collection(collect_name)
        self.user_id = user_id

    def store_profile(self, data):
        self.doc_profile = self.collect_root.document(self.user_id)
        result = self.doc_profile.set(data)
        print("profile document stored.")
        print(result)
        self.collect_activities = self.doc_profile.collection('activities')
        print("activities collection created.\n")
    
    def store_activities(self, data, doc_name):
        result = self.collect_activities.document(doc_name).set(data)
        print(doc_name + " document stored.")
        print(result)

    def log(name):
        print(name + " stored.")
