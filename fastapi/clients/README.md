# Clients Overview: S3Client and OpenAIClient

This documentation describes two reusable Python client classes used for interacting with AWS S3 and OpenAI APIs. Each class is built with robust validation, configuration via YAML, and production-grade error handling.

---

## S3Client

A reusable, production-grade S3 utility class that handles structured/unstructured file I/O, ZIP handling, and logging. Configurable via a YAML file.

### Configuration

Use a YAML config file to define credentials, bucket name, logical keys, and prefixes.

```yaml
type: role | key | session
aws_access_key_id: your-key-id        # required for key/session types
aws_secret_access_key: your-secret    # required for key/session types
aws_session_token: your-token         # required only for session type
bucket: your-bucket-name
prefixes:
  prefix1: path/to/prefix
keys:
  key1: path/to/key1.yaml
```

### Key Features

- Credentials validated on init
- Automatic retries via `tenacity`
- Pandas support for tabular data
- Safe ZIP handling
- Custom YAML, code, and log I/O

### Public Methods

#### Configuration Access
- `client`: Returns the underlying `boto3` client.
- `prefixes`: Returns configured prefixes.
- `keys`: Returns configured keys.
- `get_key(key_name)`: Returns S3 path for logical key.
- `get_prefix(prefix_name)`: Returns S3 prefix for logical name.

#### Reading
- `read_yaml(key)`: Load a YAML file from S3.
- `read_code(key)`: Load a code file (e.g. Python) and strip markdown fencing.
- `read_log(key)`: Load raw log text.
- `read_tabular(key)`: Auto-load CSV/XLSX/SAS to DataFrame.
- `read_tabulars_from_zip(zip_key, inner_paths)`: Read multiple files from ZIP into DataFrames.
- `list_keys(prefix=None, endswith=None)`: List all non-folder objects.
- `list_zip_contents(zip_key)`: List inner files in ZIP.

#### Writing
- `write_log(key, content)`: Save a string log to S3.
- `write_dataframe(df, key, format)`: Write DataFrame as CSV or Parquet.
- `write_yaml(data, key)`: Dump dict/list to S3 as YAML.
- `write_code(prefix, code, filename)`: Save code under a prefix.
- `copy_key(source_key, destination_key)`: Copy one S3 key to another.

#### Deletion
- `delete_key(key)`: Deletes the specified object.

---

## OpenAIClient

A modern wrapper for OpenAI’s Chat Completions API with structured YAML configuration, token handling, and retry logic.

### Configuration

Configure the client using a YAML file:

```yaml
env: dev
api_key: your-api-key
model: gpt-4o-mini
temperature: 0.2
max_tokens_per_message: 16384
max_tokens_per_chat: 120000
```

### Key Features

- Token counting via `tiktoken`
- Chat message formatting
- Response streaming and JSON parsing
- Retry logic via `tenacity`

### Public Methods

#### General Properties
- `client`: OpenAI client object.
- `model`: Model name used.
- `max_tokens_per_message`: Max tokens per response.
- `max_tokens_per_chat`: Max tokens per chat.

#### Token Utilities
- `token_count_for_message(message)`: Count tokens in one message.
- `token_count_for_chat(messages)`: Count total tokens.
- `is_near_limit_message(message)`: Checks message token threshold.
- `is_near_limit_chat(messages)`: Checks chat token threshold.

#### LLM Interactions
- `get_text(prompt, role='user', messages=None)`: Return plain text completion.
- `get_json(prompt, output_struct, role='user', messages=None)`: Return structured JSON.
- `get_tool_calls(prompt, tools, role='user', messages=None)`: Return tool call objects.
- `get_python(prompt, role='user', messages=None)`: Return raw Python code (markdown fence removed).

#### Logging / Formatting
- `format_messages(messages, max_length=1000)`: Pretty print messages for logs.

---

## Teardown Helpers (Internal)
- `S3Client._teardown()`: Reset boto3 client.
- `OpenAIClient._teardown()`: Nullifies OpenAI client on error.

---

## Notes

- Both clients use `tenacity.retry()` for basic retry logic with exponential backoff.
- All file paths are relative to the bucket root, using logical names defined in the YAML.
- Pandas-based I/O assumes basic formats: `.csv`, `.xlsx`, `.sas7bdat`.

---

## LLM Usage Tips

If you’re an LLM being asked to generate or interact with these clients:

- Reference method names explicitly (e.g., `write_yaml`, `read_tabulars_from_zip`)
- Assume config YAML is loaded locally and paths are correct
- Use `get_prefix()` or `get_key()` to construct dynamic keys
- Use `get_tool_calls()` for structured responses involving tools