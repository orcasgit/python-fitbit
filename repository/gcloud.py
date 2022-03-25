# Import the Secret Manager client library.
from google.cloud import secretmanager
import google_crc32c
import json

class GoogleCloud():
    def __init__(self, project_id) -> None:
        self.client = secretmanager.SecretManagerServiceClient()
        pass

    def _verify_checksum(self, response):
        # Verify payload checksum.
        crc32c = google_crc32c.Checksum()
        crc32c.update(response.payload.data)
        if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
            print("Data corruption detected.")
            return response

    def get_secrets(self, project_id, filter = "labels.domain:fitbit AND labels.type:fitbit-user"):
        self.project_id = project_id
        self.parent = f"projects/{project_id}"

        # List all secrets.
        for secret in self.client.list_secrets(request={"parent": self.parent, "filter": filter}):
            print("Found secret: {}".format(secret.name))
            name = f"{secret.name}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            response = self._verify_checksum(response)
            payload = json.loads(response.payload.data.decode("UTF-8"))

foo = GoogleCloud()
foo.get_secrets("tigerawaredev")