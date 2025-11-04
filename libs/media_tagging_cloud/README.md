# Media Tagging Cloud Function

This document provides instructions on how to deploy the Media Tagging solution to Google Cloud Platform. The deployment process is automated via the `setup.sh` script.

## Function Overview

The Cloud Function (`media_tagging`) processes media files (videos or images) stored in Google Cloud Storage. It uses a generative AI model to either generate descriptions or apply specific tags based on a custom schema. The function can be triggered via an HTTP request or a Pub/Sub message.

### Input Payload

The function expects a JSON payload with the following structure. See `request.json` for a complete example.

| Parameter                | Type     | Required | Description                                                                                                                            |
| ------------------------ | -------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `asset_ids`              | `array`  | Yes      | A list of asset filenames to be processed from the `assets_gcs_folder`.                                                                |
| `assets_gcs_folder`      | `string` | Yes      | The GCS path (e.g., `gs://your-bucket/media/`) where the asset files are located.                                                        |
| `tagging_mode`           | `string` | Yes      | The operation to perform. Can be `describe` (generate a description) or `tag` (apply tags based on a schema).                            |
| `output_gcs_folder`      | `string` | Yes      | The GCS path where the output JSON file and logs will be saved.                                                                        |
| `job_id`                 | `string` | No       | A unique identifier for the job. If provided, the output file will be named `{job_id}.json` and a log file will be created.              |
| `custom_prompt_gcs_path` | `string` | No       | A GCS path to a text file containing a custom prompt to use for tagging.                                                               |
| `custom_schema`          | `object` | No       | A JSON schema object that defines the structure of the tags to be extracted. Required when `tagging_mode` is `tag`.                      |
| `media_type`             | `string` | No       | The type of media to process. Can be `VIDEO` or `IMAGE`. Defaults to `VIDEO`.                                                          |

## Prerequisites

1.  **Google Cloud SDK:** Ensure you have the `gcloud` command-line tool installed and authenticated.
2.  **Project Permissions:** The user running the script must have `Owner` or `Admin` permissions on the target GCP project. This is required for setting the necessary IAM permissions for the services.
3.  **Gemini API Key:** You must have a valid Gemini API key.

## Configuration

The deployment script uses a `settings.ini` file for configuration.

### Recommended Configuration

For a standard deployment using Pub/Sub as a trigger and Google Secret Manager for the API key, your `settings.ini` should look like this:

```ini
[common]
  region=europe-west1 # Or your preferred GCP region

[functions]
  memory=512
  trigger=pubsub
  use-secret-manager=true

[pubsub]
  topic=tag_media
```

-   `use-secret-manager=true`: This tells the script to map a secret from Secret Manager to the `GEMINI_API_KEY` environment variable in the Cloud Function.
-   `trigger=pubsub`: Configures the function to be triggered by messages on a Pub/Sub topic.
-   `topic=tag_media`: Specifies the name of the Pub/Sub topic to use.

## Deployment Steps

### Step 1: Create the API Key Secret

Before deploying, you must store your Gemini API key in Google Secret Manager. The script can do this for you.

Run the following command, replacing `YOUR_API_KEY` with your actual key:

```bash
./setup.sh create_secret --secret gemini-api-key --value YOUR_API_KEY
```

This command creates a secret named `gemini-api-key` with your key as its value. If the secret already exists, it will add a new version.

### Step 2: Deploy the Solution

After configuring `settings.ini` and creating the secret, you can deploy all the necessary components by running:

```bash
./setup.sh deploy_all
```

This command will:
1.  Enable the required Google Cloud APIs (Secret Manager, Artifact Registry, Cloud Run).
2.  Set the necessary IAM permissions for the service account.
3.  Deploy the Cloud Function with the configuration specified in `settings.ini`.

## Available Script Commands

The `setup.sh` script provides several functions for managing the deployment. To see a list of all available commands, run the script without any arguments:

```bash
./setup.sh
```

This will output a list of functions you can call, such as `enable_apis`, `set_iam_permissions`, `deploy_functions`, and `deploy_all`.