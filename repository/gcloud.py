# Import the Secret Manager client library.
from google.cloud import secretmanager

class GoogleCloud():
    def __init__(self) -> None:
        pass

    def get_secrets(project_id):
        """
        List all secrets in the given project.
        """

        # Create the Secret Manager client.
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the parent project.
        parent = f"projects/{project_id}"

        # List all secrets.
        for secret in client.list_secrets(request={"parent": parent}):
            print("Found secret: {}".format(secret.name))
