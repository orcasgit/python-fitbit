from repository.gcloud import GoogleCloud

class GoogleCloudRepository:
    def __init__(self, gc: GoogleCloud) -> None:
        self.gc = gc
        pass

    def get_firebase_credential(self, project_id):
        credentials = self.gc.get_secrets(project_id=project_id,filter="labels.domain:fitbit AND labels.type:firebase-config AND labels.id:credentials")
        return credentials[0]

    def get_realtime_db_url(self, project_id):
        credentials = self.gc.get_secrets(project_id=project_id,filter="labels.domain:fitbit AND labels.type:firebase-config AND labels.id:db-url")
        return credentials[0]

    def get_users_secrets(self, project_id):
        users_secrets = self.gc.get_secrets(project_id=project_id)