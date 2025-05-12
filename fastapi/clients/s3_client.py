import re
import textwrap
import boto3
import yaml
import logging
import io
import zipfile
import pandas as pd
import json

from typing import Optional, List, Dict, Union
from pathlib import Path
from pydantic import BaseModel, Field, model_validator
from botocore.exceptions import BotoCoreError, ClientError
from tenacity import retry, stop_after_attempt, wait_exponential


class S3Config(BaseModel):
    type: str = Field(..., pattern="^(role|key|session)$")
    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]
    aws_session_token: Optional[str]
    bucket: str
    prefixes: Dict[str, str]
    keys: Dict[str, str]

    @model_validator(mode="after")
    def check_credentials(self) -> 'S3Config':
        """
        Validate that the appropriate credentials are present based on the `type`.
        """
        if self.type == "key":
            if not self.aws_access_key_id or not self.aws_secret_access_key:
                raise ValueError("aws_access_key_id and aws_secret_access_key are required for key-based auth")
        if self.type == "session":
            if not (self.aws_access_key_id and self.aws_secret_access_key and self.aws_session_token):
                raise ValueError("All AWS credentials including session token are required for session-based auth")
        return self


class S3Client:
    """
    Reusable S3 client class with built-in configuration handling, validation, 
    retry logic, and data I/O capabilities for structured and unstructured content.
    """

    def __init__(self, config_path: Union[str, Path]):
        """
        Initialize the S3 client using a local YAML configuration file.

        Parameters:
        - config_path: Path to the YAML configuration file.
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self._config = config 
        self._keys = config['keys']
        self._prefixes = config['prefixes']
        self._bucket = config['bucket']
        self._type = config['type']

        if self._type == 'role':
            self._s3: boto3.client = boto3.client('s3')
        elif self._type == 'key':
            self._s3: boto3.client = boto3.client(
                's3',
                aws_access_key_id=config['aws_access_key_id'],
                aws_secret_access_key=config['aws_secret_access_key'])
        elif self._type == 'session':
            self._s3: boto3.client = boto3.client(
                's3',
                aws_access_key_id=config['aws_access_key_id'],
                aws_secret_access_key=config['aws_secret_access_key'],
                aws_session_token=config['aws_session_token'])
        else:
            self._s3 = boto3.client('s3')
        self._validate_connection()  # Fast failure if S3 unreachable

    @property
    def prefixes(self) -> Dict[str, str]:
        """Return the configured S3 prefixes."""
        return self._prefixes
    
    @property
    def keys(self) -> Dict[str, str]:
        """Return the configured S3 keys."""
        return self._keys
    
    @property
    def client(self) -> Dict[str, str]:
        """Return the configured S3 client."""
        return self._s3

    def _validate_connection(self):
        """
        Attempt a lightweight connection to S3 to ensure credentials and internet are valid.
        Raises an error immediately if S3 is unreachable.
        """
        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except ClientError as e:
            raise ConnectionError(f"Unable to connect to S3 bucket '{self._bucket}': {e}")
        except Exception as e:
            raise ConnectionError(f"S3 connectivity validation failed: {e}")
    
    def get_key(self, key_name: str) -> str:
        """
        Return the full key path for a given logical key name from config.

        Parameters:
        - key_name: Logical key identifier defined in the config.

        Returns:
        - Full S3 key path.
        """
        key = self._keys.get(key_name, None)
        if not key:
            self._teardown()
            raise ValueError(f"S3 ERROR: Requested key {key_name} not found.")
        return key

    def get_prefix(self, prefix_name: str) -> str:
        """
        Return the full prefix path for a given logical prefix name from config.

        Parameters:
        - prefix_name: Logical prefix identifier defined in the config.

        Returns:
        - Full S3 prefix path.
        """
        prefix = self._prefixes.get(prefix_name, None)
        if not prefix:
            raise ValueError(f"S3 ERROR: Requested prefix {prefix_name} not found.")
        return prefix

    @retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=1, max=10))
    def read_yaml(self, key: str) -> Dict:
        """
        Read a YAML file from the given S3 key and return its contents as a dictionary.
        """
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=key)
            return self._parse_yaml_bytes(obj['Body'].read())
        except self._s3.exceptions.NoSuchKey:
            raise ValueError(f"No such key: {key}")
            #return {}
        except ValueError as e:
            raise ValueError(f"YAML parsing error for {key}: {e}")
            #return {}
        except Exception as e:
            raise ValueError(f"Unexpected error retrieving {key}: {e}")
            return {}

    @retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=1, max=10))
    def read_code(self, key: str) -> str:
        """
        Read a code file (e.g., Python) from the given S3 key and return it as a string.

        Parameters:
        - key: Full S3 key to the code file.

        Returns:
        - Contents of the file as a string.
        """
        response = self._s3.get_object(Bucket=self._bucket, Key=key)
        formatted_text = textwrap.dedent(response['Body'].read().decode('utf-8')).strip()
        cleaned_text = re.sub(
            pattern=r"^```[a-z]*\s*|```$",
            repl="", 
            string=formatted_text.strip(), 
            flags=re.IGNORECASE | re.MULTILINE).strip()
        return cleaned_text

    @retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=1, max=10))
    def read_log(self, key: str) -> str:
        """
        Read a log file from the given S3 key and return its content.

        Parameters:
        - key: Full S3 key to the log file.

        Returns:
        - Log content as a string.
        """
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=key)
            return obj['Body'].read().decode('utf-8')
        except self._s3.exceptions.NoSuchKey:
            raise ValueError(f"No such log file: {key}")
            #return ""
        except Exception as e:
            self._teardown()
            raise ValueError(f"Error retrieving log from {key}: {e}")
            #return ""
        

    @retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=1, max=10))
    def write_log(self, key: str, content: str) -> None:
        """
        Write log content to a given S3 key.

        Parameters:
        - key: Full S3 key to write to.
        - content: Log content as a string.
        """
        pass
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=content.encode('utf-8'))


    def list_keys(self, prefix: Optional[str] = None, endswith: Optional[str] = None) -> List[str]:
        """
        List non-folder keys (files) under a given prefix in the S3 bucket.

        Parameters:
        - prefix: Optional prefix to filter objects by path.
        - endswith: Optional suffix filter to match file types.

        Returns:
        - List of matching keys.
        """
        paginator = self._s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=self._bucket, Prefix=prefix)

        matching_keys = []
        for page in page_iterator:
            contents = page.get('Contents', [])
            for obj in contents:
                key = obj['Key']
                if endswith and not key.endswith(endswith):
                    continue
                if key.endswith('/'):
                    continue
                matching_keys.append(key)
        return matching_keys

    def list_zip_contents(self, zip_key: str) -> List[Dict[str, str]]:
        """
        Return a list of files inside a zip file stored in S3, including both full paths and file names.

        Parameters:
        - zip_key: S3 key pointing to a .zip file.

        Returns:
        - List of dictionaries with 'path' and 'filename' for each file in the archive.
        """
        zip_obj = self._s3.get_object(Bucket=self._bucket, Key=zip_key)
        with zipfile.ZipFile(io.BytesIO(zip_obj['Body'].read())) as z:
            return [
                {
                    "path": file_path,
                    "filename": file_path.split('/')[-1]
                }
                for file_path in z.namelist()
                if not file_path.endswith('/')  # skip directories
            ]

    def read_tabulars_from_zip(self, zip_key: str, inner_paths: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Extract multiple tabular files from a zip archive in S3 and return them as pandas DataFrames.

        Parameters:
        - zip_key: S3 key to the .zip archive.
        - inner_paths: List of relative file paths inside the zip archive.

        Returns:
        - Dictionary where keys are file paths and values are corresponding DataFrames.
        """
        zip_obj = self._s3.get_object(Bucket=self._bucket, Key=zip_key)
        with zipfile.ZipFile(io.BytesIO(zip_obj['Body'].read())) as z:
            extracted = {}

            for path in inner_paths:
                if path not in z.namelist():
                    raise FileNotFoundError(f"File {path} not found in zip: {zip_key}")

                with z.open(path) as f:
                    raw_bytes = f.read()
                    extension = Path(path).suffix.lower()
                    extracted[path] = self._read_tabular_bytes(raw_bytes, extension)

            return extracted

    def read_tabular(self, key: str) -> pd.DataFrame:
        """
        Read a tabular file (CSV, XLSX, or SAS7BDAT) from S3 and return a DataFrame.
        """
        obj = self._s3.get_object(Bucket=self._bucket, Key=key)
        file_bytes = obj['Body'].read()
        extension = Path(key).suffix.lower()
        return self._read_tabular_bytes(file_bytes, extension)

    def write_dataframe(self, df: pd.DataFrame, key: str, file_format: str = 'csv') -> None:
        """
        Write a pandas DataFrame to S3 in the specified format.

        Parameters:
        - df: DataFrame to write.
        - key: Destination S3 key.
        - file_format: File format to use ("csv", "parquet", etc.).
        """
        if file_format == 'csv':
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            body = buffer.getvalue()
        elif file_format == 'parquet':
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            body = buffer.getvalue()
        else:
            self._teardown()
            raise ValueError(f"Unsupported format: {file_format}")

        self._s3.put_object(Bucket=self._bucket, Key=key, Body=body)

    def copy_key(self, source_key: str, destination_key: str) -> None:
        """
        Copy a file from one key to another within the same S3 bucket.

        Parameters:
        - source_key: The full S3 key of the source file.
        - destination_key: The full S3 key where the file should be copied to.
        """
        try:
            copy_source = {
                'Bucket': self._bucket,
                'Key': source_key
            }
            self._s3.copy_object(
                Bucket=self._bucket,
                CopySource=copy_source,
                Key=destination_key
            )
        except ClientError as e:
            raise ValueError(f"Failed to copy from {source_key} to {destination_key}: {e}")


    def write_code(self, prefix: str, code: str, filename: str) -> None:
        """
        Write a code string to an S3 prefix under the specified file name.

        Parameters:
        - prefix: S3 prefix (folder path).
        - code: Code content as a string.
        - filename: Desired filename to write as.
        """
        key = f"{prefix}/{filename}"
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=code)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=10))
    def write_yaml(self, data: Union[Dict, List], key: str) -> None:
        """
        Write a Python dictionary or list as a YAML file to S3.

        Parameters:
            data (dict or list): Data to serialize into YAML.
            key (str): Full S3 key where the YAML file will be written.

        Raises:
            ValueError: If serialization or upload fails.
        """
        try:
            yaml_str = yaml.safe_dump(data, sort_keys=False)
            self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=yaml_str.encode('utf-8'),
                ContentType='text/yaml'
            )
        except Exception as e:
            raise ValueError(f"Failed to write YAML to S3 at key {key}: {e}")

    def _log(self, message: str, level: str = "info") -> None:
        """
        Internal method to log messages with appropriate level.

        Parameters:
        - message: Log message.
        - level: Logging level ("info", "error", etc.).
        """
        pass

    @staticmethod
    def _parse_yaml_bytes(data: bytes) -> Dict:
        """
        Convert a YAML byte string to a Python dictionary.

        Parameters:
        - data: YAML content as bytes.

        Returns:
        - Parsed dictionary.
        """
        try:
            return yaml.safe_load(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML: {e}")

    @staticmethod
    def _read_tabular_bytes(data: bytes, extension: str) -> pd.DataFrame:
        """
        Convert tabular file bytes to a DataFrame based on extension.

        Parameters:
        - data: File contents in bytes.
        - extension: File extension (e.g., '.csv', '.sas7bdat', '.xlsx').

        Returns:
        - DataFrame parsed from the file.
        """
        buffer = io.BytesIO(data)

        if extension == '.csv':
            return pd.read_csv(buffer)
        elif extension == '.xlsx':
            return pd.read_excel(buffer)
        elif extension == '.sas7bdat':
            return pd.read_sas(buffer, format='sas7bdat', encoding='iso-8859-1')
        else:
            raise ValueError(f"Unsupported file extension: {extension}")
        
    def delete_key(self, key):
        self._s3.delete_object(
            Bucket=self._bucket,
            Key=key
        )
        
    def _teardown(self):
        self._s3 = None


    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=10))
    def read_json(self, key: str) -> Union[Dict, List]:
        """
        Read a JSON file from S3 and return it as a Python dictionary or list.

        Parameters:
        - key: Full S3 key path to the JSON file.

        Returns:
        - Parsed JSON object (dict or list).
        """
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
            body = response['Body'].read().decode('utf-8')
            return json.loads(body)
        except self._s3.exceptions.NoSuchKey:
            raise FileNotFoundError(f"No such JSON key: {key}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON at {key}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error reading JSON from {key}: {e}")


    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=10))
    def write_json(self, key: str, data: Union[Dict, List]) -> None:
        """
        Write a Python dictionary or list as a JSON file to S3.

        Parameters:
        - key: Full S3 key path to write to.
        - data: Data to serialize and upload.
        """
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=json_str.encode('utf-8'),
                ContentType='application/json'
            )
        except Exception as e:
            raise RuntimeError(f"Failed to write JSON to S3 at key {key}: {e}")