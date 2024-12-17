# `dreadnode`

Interact with the Dreadnode platform

**Usage**:

```console
$ dreadnode [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `agent`: Interact with Strike agents
* `challenge`: Interact with Crucible challenges
* `login`: Authenticate to the platform.
* `profile`: Manage server profiles
* `refresh`: Refresh data for the active server profile.
* `version`: Show versions and exit.

## `dreadnode agent`

Interact with Strike agents

**Usage**:

```console
$ dreadnode agent [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `clone`: Clone a github repository
* `deploy`: Start a new run using the latest active...
* `init`: Initialize a new agent project
* `latest`: Show the latest run of the active agent
* `links`: List available agent links
* `models`: List available models for the current (or...
* `push`: Push a new version of the active agent
* `runs`: List runs for the active agent
* `show`: Show the status of the active agent
* `strikes`: List available strikes
* `switch`: Switch to a different agent link
* `templates`: Interact with Strike templates
* `versions`: List historical versions of the active agent

### `dreadnode agent clone`

Clone a github repository

**Usage**:

```console
$ dreadnode agent clone [OPTIONS] REPO [TARGET]
```

**Arguments**:

* `REPO`: Repository name or URL  [required]
* `[TARGET]`: The target directory

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent deploy`

Start a new run using the latest active agent version

**Usage**:

```console
$ dreadnode agent deploy [OPTIONS]
```

**Options**:

* `-m, --model TEXT`: The inference model to use for this run
* `-d, --dir DIRECTORY`: The agent directory  [default: .]
* `-s, --strike TEXT`: The strike to use for this run
* `-w, --watch`: Watch the run status  [default: True]
* `--help`: Show this message and exit.

### `dreadnode agent init`

Initialize a new agent project

**Usage**:

```console
$ dreadnode agent init [OPTIONS] STRIKE
```

**Arguments**:

* `STRIKE`: The target strike  [required]

**Options**:

* `-d, --dir DIRECTORY`: The directory to initialize  [default: .]
* `-n, --name TEXT`: The project name (used for container naming)
* `-t, --template TEXT`: The template to use for the agent
* `-s, --source TEXT`: Initialize the agent using a custom template from a github repository, ZIP archive URL or local folder
* `-p, --path TEXT`: If --source has been provided, use --path to specify a subfolder to initialize from
* `--help`: Show this message and exit.

### `dreadnode agent latest`

Show the latest run of the active agent

**Usage**:

```console
$ dreadnode agent latest [OPTIONS]
```

**Options**:

* `-d, --dir DIRECTORY`: The agent directory  [default: .]
* `-v, --verbose`: Show detailed run information
* `-l, --logs`: Show all container logs for the run (only in verbose mode)
* `--raw`: Show raw JSON output
* `--help`: Show this message and exit.

### `dreadnode agent links`

List available agent links

**Usage**:

```console
$ dreadnode agent links [OPTIONS] [DIRECTORY]
```

**Arguments**:

* `[DIRECTORY]`: The agent directory  [default: .]

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent models`

List available models for the current (or specified) strike

**Usage**:

```console
$ dreadnode agent models [OPTIONS] [DIRECTORY]
```

**Arguments**:

* `[DIRECTORY]`: The agent directory  [default: .]

**Options**:

* `-s, --strike TEXT`: The strike to query
* `--help`: Show this message and exit.

### `dreadnode agent push`

Push a new version of the active agent

**Usage**:

```console
$ dreadnode agent push [OPTIONS]
```

**Options**:

* `-d, --dir DIRECTORY`: The agent directory  [default: .]
* `-t, --tag TEXT`: The tag to use for the image
* `-e, --env-var TEXT`: Environment vars to use when executing the image (key=value)
* `-n, --new`: Create a new agent instead of a new version
* `-m, --message TEXT`: Notes for the new version
* `-r, --rebuild`: Force rebuild the agent image
* `--help`: Show this message and exit.

### `dreadnode agent runs`

List runs for the active agent

**Usage**:

```console
$ dreadnode agent runs [OPTIONS] [DIRECTORY]
```

**Arguments**:

* `[DIRECTORY]`: The agent directory  [default: .]

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent show`

Show the status of the active agent

**Usage**:

```console
$ dreadnode agent show [OPTIONS]
```

**Options**:

* `-d, --dir DIRECTORY`: The agent directory  [default: .]
* `--help`: Show this message and exit.

### `dreadnode agent strikes`

List available strikes

**Usage**:

```console
$ dreadnode agent strikes [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent switch`

Switch to a different agent link

**Usage**:

```console
$ dreadnode agent switch [OPTIONS] AGENT_OR_PROFILE [DIRECTORY]
```

**Arguments**:

* `AGENT_OR_PROFILE`: Agent key/id or profile name  [required]
* `[DIRECTORY]`: The agent directory  [default: .]

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent templates`

Interact with Strike templates

**Usage**:

```console
$ dreadnode agent templates [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `install`: Install a template pack
* `show`: List available agent templates with their...

#### `dreadnode agent templates install`

Install a template pack

**Usage**:

```console
$ dreadnode agent templates install [OPTIONS] [SOURCE]
```

**Arguments**:

* `[SOURCE]`: The source of the template pack  [default: dreadnode/basic-agents]

**Options**:

* `--help`: Show this message and exit.

#### `dreadnode agent templates show`

List available agent templates with their descriptions

**Usage**:

```console
$ dreadnode agent templates show [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent versions`

List historical versions of the active agent

**Usage**:

```console
$ dreadnode agent versions [OPTIONS] [DIRECTORY]
```

**Arguments**:

* `[DIRECTORY]`: The agent directory  [default: .]

**Options**:

* `--help`: Show this message and exit.

## `dreadnode challenge`

Interact with Crucible challenges

**Usage**:

```console
$ dreadnode challenge [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `artifact`: Download a challenge artifact.
* `list`: List challenges
* `submit-flag`: Submit a flag to a challenge

### `dreadnode challenge artifact`

Download a challenge artifact.

**Usage**:

```console
$ dreadnode challenge artifact [OPTIONS] CHALLENGE_ID ARTIFACT_NAME
```

**Arguments**:

* `CHALLENGE_ID`: Challenge name  [required]
* `ARTIFACT_NAME`: Artifact name  [required]

**Options**:

* `-o, --output DIRECTORY`: The directory to save the artifact to.  [default: .]
* `--help`: Show this message and exit.

### `dreadnode challenge list`

List challenges

**Usage**:

```console
$ dreadnode challenge list [OPTIONS]
```

**Options**:

* `--sort-by [none|difficulty|status|title|authors|tags]`: The sorting order  [default: none]
* `--sort-order [ascending|descending]`: The sorting order  [default: ascending]
* `--help`: Show this message and exit.

### `dreadnode challenge submit-flag`

Submit a flag to a challenge

**Usage**:

```console
$ dreadnode challenge submit-flag [OPTIONS] CHALLENGE FLAG
```

**Arguments**:

* `CHALLENGE`: Challenge name  [required]
* `FLAG`: Challenge flag  [required]

**Options**:

* `--help`: Show this message and exit.

## `dreadnode login`

Authenticate to the platform.

**Usage**:

```console
$ dreadnode login [OPTIONS]
```

**Options**:

* `-s, --server TEXT`: URL of the server
* `-p, --profile TEXT`: Profile alias to assign / update
* `--help`: Show this message and exit.

## `dreadnode profile`

Manage server profiles

**Usage**:

```console
$ dreadnode profile [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `forget`: Remove a server profile
* `list`: List all server profiles
* `switch`: Set the active server profile

### `dreadnode profile forget`

Remove a server profile

**Usage**:

```console
$ dreadnode profile forget [OPTIONS] PROFILE
```

**Arguments**:

* `PROFILE`: Profile of the server to remove  [required]

**Options**:

* `--help`: Show this message and exit.

### `dreadnode profile list`

List all server profiles

**Usage**:

```console
$ dreadnode profile list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `dreadnode profile switch`

Set the active server profile

**Usage**:

```console
$ dreadnode profile switch [OPTIONS] PROFILE
```

**Arguments**:

* `PROFILE`: Profile to switch to  [required]

**Options**:

* `--help`: Show this message and exit.

## `dreadnode refresh`

Refresh data for the active server profile.

**Usage**:

```console
$ dreadnode refresh [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `dreadnode version`

Show versions and exit.

**Usage**:

```console
$ dreadnode version [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
