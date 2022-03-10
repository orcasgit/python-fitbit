from firebase_admin import db

from repository.local_storage import LocalStorage

class Realtime(LocalStorage):
    def __init__(self, root):
        super().__init__("Realtime Database")
        self.root = root


    def store_profile(self, data):
        self.ref = db.reference(self.root + "/" + data['encodedId'])
        self.ref.set(data)
    
    def store_activities(self, data, doc_name):
        self.ref.child("activities").child(doc_name).set(data)
        super()._log(doc_name)

    def store_intraday(self, data, date, doc_name):
        self.ref.child("intraday").child(date.strftime('%Y-%m-%d')).child(doc_name).set(data)
        super()._log(doc_name)

    def store_time_series(self, data, doc_name):
        self.ref.child("time_series").child(doc_name).set(data)
        super()._log(doc_name)