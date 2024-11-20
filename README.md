Dreadnode command line interface.

## Installation

### With Poetry:

This project is packaged for and meant to be used with the [Poetry package management tool](https://python-poetry.org/).

To install the project dependencies:

```bash
poetry install
```

And then enter its shell:

```bash
poetry shell
```

### With Docker:

Alternatively, you can build a docker image and run the CLI from a container:

```bash
docker build -t dreadnode .
```

Whenever using the CLI from a docker container, remember to share your user configuration, the network from the host and mount the docker socket:

```bash
docker run -it \
    --net=host \
    -v/var/run/docker.sock:/var/run/docker.sock \
    -v$HOME/.dreadnode:/root/.dreadnode \
    dreadnode --help
```

Optionally, you can create a bash alias like so:

```bash
alias dreadnode='docker run -it --net=host -v/var/run/docker.sock:/var/run/docker.sock -v$HOME/.dreadnode:/root/.dreadnode dreadnode'
```

## Usage

> [!NOTE]
> For a full list of commands and options, see the [CLI.md](./CLI.md) file.

Help menu:

```bash
dreadnode --help
```

Show version:

```bash
dreadnode version
```

Authenticate:

```bash
dreadnode login
```

Authenticate to a specific server:

```bash
dreadnode login --server https://dev-crucible.dreadnode.io
```

Manage server profiles with:

```bash
# list all profiles
dreadnode profile list

# switch to a named profile
dreadnode profile switch <profile_name>

# remove a profile
dreadnode profile forget <profile_name>
```

Interact with the Crucible challenges:

```bash
# list all challenges
dreadnode challenge list

# download an artifact
dreadnode challenge artifact <challenge_id> <artifact_name> -o <output_path>

# submit a flag
dreadnode challenge submit-flag <challenge_id> 'gAAAAA...'
```

Interact with Strike agents:

```bash
# list all strikes
dreadnode agent strikes

# list all available templates with their descriptions
dreadnode agent templates

# initialize a new agent in the current directory
dreadnode agent init -t <template_name> <strike_id> 

# initialize a new agent in the specified directory
dreadnode agent init -t <template_name> <strike_id> --dir <directory>

# push a new version of the agent
dreadnode agent push

# start a new run using the latest agent version.
dreadnode agent deploy

# show the latest run of the currently active agent
dreadnode agent latest

# list all available links
dreadnode agent links

# list available models for the current strike
dreadnode agent models

# list all runs for the currently active agent  
dreadnode agent runs

# show the status of the currently active agent
dreadnode agent show

# list historical versions of this agent
dreadnode agent versions

# switch/link to a different agent
dreadnode agent switch <agent_id>
```
