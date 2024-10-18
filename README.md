Dreadnode command line interface.

## Installation

### With Poetry:

```bash
poetry install 
```

Then enter the poetry shell:

```bash
poetry shell
```

### With Docker:

```bash
docker build -t dreadnode .
```

and then run:

```bash
docker run -it dreadnode --help
```

## Usage

Help menu:

```bash
dreadnode --help
```

Authenticate:

```bash
dreadnode login
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


