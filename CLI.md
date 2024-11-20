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

* `deploy`: Start a new run using the latest agent...
* `init`: Initialize a new agent project
* `latest`: Show the latest run of the currently...
* `links`: List all available links
* `models`: List available models for the current (or...
* `push`: Push a new version of the agent.
* `runs`: List all runs for the currently active agent
* `show`: Show the status of the currently active agent
* `strikes`: List all strikes
* `switch`: Switch/link to a different agent
* `templates`: List all available templates with their...
* `versions`: List historical versions of this agent

### `dreadnode agent deploy`

Start a new run using the latest agent version

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
* `-t, --template [rigging_basic|rigging_loop|nerve_basic]`: The template to use for the agent  [default: rigging_basic]
* `--source TEXT`: Initialize the agent using a custom template from a github repository, ZIP archive URL or local folder
* `--help`: Show this message and exit.

### `dreadnode agent latest`

Show the latest run of the currently active agent

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

List all available links

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

Push a new version of the agent.

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
* `--help`: Show this message and exit.

### `dreadnode agent runs`

List all runs for the currently active agent

**Usage**:

```console
$ dreadnode agent runs [OPTIONS] [DIRECTORY]
```

**Arguments**:

* `[DIRECTORY]`: The agent directory  [default: .]

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent show`

Show the status of the currently active agent

**Usage**:

```console
$ dreadnode agent show [OPTIONS]
```

**Options**:

* `-d, --dir DIRECTORY`: The agent directory  [default: .]
* `--help`: Show this message and exit.

### `dreadnode agent strikes`

List all strikes

**Usage**:

```console
$ dreadnode agent strikes [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent switch`

Switch/link to a different agent

**Usage**:

```console
$ dreadnode agent switch [OPTIONS] AGENT [DIRECTORY]
```

**Arguments**:

* `AGENT`: Agent key or id  [required]
* `[DIRECTORY]`: The agent directory  [default: .]

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent templates`

List all available templates with their descriptions

**Usage**:

```console
$ dreadnode agent templates [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `dreadnode agent versions`

List historical versions of this agent

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
