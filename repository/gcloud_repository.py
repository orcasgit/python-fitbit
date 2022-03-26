
from .gcloud import GoogleCloud


class GoogleCloudRepository:
    def __init__(self, gc: GoogleCloud) -> None:
        self.gc = gc

    def get_firebase_credential(self):
        credentials = self.gc.get_secrets(
            filter="labels.domain:fitbit AND labels.type:firebase-config AND labels.id:credentials")
        return credentials[0]

    def get_realtime_db_url(self):
        credentials = self.gc.get_secrets(
            filter="labels.domain:fitbit AND labels.type:firebase-config AND labels.id:db-url")
        return credentials[0]

    def get_users_secrets(self):
        users_secrets = self.gc.get_secrets()
        return users_secrets

    def add_secret_version(self, secret_id, payload):
        old_payload = self.gc.get_secret(secret_id)
        new_payload = old_payload
        new_payload.update(payload)
        self.gc.add_secret_version(new_payload)
