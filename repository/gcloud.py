# Import the Secret Manager client library.
from google.cloud import secretmanager
import google_crc32c
import json


class GoogleCloud():
    def __init__(self, project_id) -> None:
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id
        self.parent = f"projects/{project_id}"

    def _verify_checksum(self, response):
        # Verify payload checksum.
        crc32c = google_crc32c.Checksum()
        crc32c.update(response.payload.data)
        if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
            print("Data corruption detected.")

        return response

    def get_secrets(
            self,
            filter="labels.domain:fitbit AND labels.type:fitbit-user"):
        secrets = self.client.list_secrets(
            request={"parent": self.parent, "filter": filter})
        payloads = []

        for secret in secrets:
            payload = self.get_secret(secret.name)
            payloads.append(payload)

        return payloads

    def get_secret(self, secret_id):
        name = f"{secret_id}/versions/latest"
        response = self.client.access_secret_version(request={"name": name})
        response = self._verify_checksum(response)
        payload = response.payload.data.decode("UTF-8")
        try:
            payload = json.loads(payload)
            payload["secret_id"] = secret_id
        except json.JSONDecodeError as e:
            pass

        return payload

    def add_secret_version(self, payload):
        # Build the resource name of the parent secret.
        parent = payload["secret_id"]

        # Convert the string payload into a bytes. This step can be omitted if you
        # pass in bytes instead of a str for the payload argument.
        payload = json.dumps(payload).encode("UTF-8")

        # Calculate payload checksum. Passing a checksum in add-version request
        # is optional.
        crc32c = google_crc32c.Checksum()
        crc32c.update(payload)

        # Add the secret version.
        response = self.client.add_secret_version(
            request={
                "parent": parent,
                "payload": {
                    "data": payload,
                    "data_crc32c": int(
                        crc32c.hexdigest(),
                        16)},
            })

        # Print the new secret version name.
        print("Added secret version: {}".format(response.name))
