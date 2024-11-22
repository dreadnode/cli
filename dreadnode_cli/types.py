import re
import typing as t


class GithubRepo(str):
    """
    A string subclass that normalizes various GitHub repository string formats.

    Supported formats:
    - Full URLs: https://github.com/owner/repo
    - SSH URLs: git@github.com:owner/repo.git
    - Simple format: owner/repo
    - With ref: owner/repo/tree/main
    - With complex ref: owner/repo/tree/feature/custom
    - With ref (URL): https://github.com/owner/repo/tree/main
    - With .git: owner/repo.git
    - Raw URLs: https://raw.githubusercontent.com/owner/repo/main
    - Release URLs: owner/repo/releases/tag/v1.0.0
    - ZIP URLs: https://github.com/owner/repo/zipball/main
    - Own format: owner/repo@ref
    """

    # Instance properties
    namespace: str
    repo: str
    ref: str

    # Regex patterns
    SSH_PATTERN = re.compile(r"git@github\.com:([^/]+)/([^/]+?)(\.git)?$")
    SIMPLE_PATTERN = re.compile(r"^([^/]+)/([^/]+?)(\.git)?$")
    URL_PATTERN = re.compile(r"github\.com/([^/]+)/([^/]+?)(?:\.git|/(?:tree|blob)/(.+?))?$")
    RAW_PATTERN = re.compile(r"raw\.githubusercontent\.com/([^/]+)/([^/]+)/(.+)")
    RELEASE_PATTERN = re.compile(r"([^/]+)/([^/]+)/releases/tag/(.+)$")
    OWN_FORMAT_PATTERN = re.compile(r"^([^/]+)/([^/@:]+)@(.+)$")
    ZIPBALL_PATTERN = re.compile(r"github\.com/([^/]+)/([^/]+?)/zipball/(.+)$")

    def __new__(cls, value: t.Any, *args: t.Any, **kwargs: t.Any) -> "GithubRepo":
        if not isinstance(value, str):
            return super().__new__(cls, str(value))

        namespace = None
        repo = None
        ref = "main"

        value = value.strip()

        # Try our own format first (owner/repo@ref)
        match = cls.OWN_FORMAT_PATTERN.match(value)
        if match:
            namespace = match.group(1)
            repo = match.group(2)
            ref = match.group(3)

        # Try as an SSH URL
        elif value.startswith("git@"):
            match = cls.SSH_PATTERN.search(value)
            if match:
                namespace, repo = match.group(1), match.group(2)

        # Try as a full URL
        elif value.startswith(("http://", "https://")):
            url_parts = value.split("//", 1)[1]

            # Try zipball pattern first
            match = cls.ZIPBALL_PATTERN.search(url_parts)
            if match:
                namespace = match.group(1)
                repo = match.group(2)
                ref = match.group(3)

            # Try raw githubusercontent pattern
            elif url_parts.startswith("raw.githubusercontent.com"):
                match = cls.RAW_PATTERN.search(url_parts)
                if match:
                    namespace, repo, ref = match.group(1), match.group(2), match.group(3)

            # Try standard GitHub URL pattern
            else:
                match = cls.URL_PATTERN.search(url_parts)
                if match:
                    namespace = match.group(1)
                    repo = match.group(2)
                    ref = match.group(3) or ref

        # Try release tag format
        elif "/releases/tag/" in value:
            match = cls.RELEASE_PATTERN.match(value)
            if match:
                namespace, repo, ref = match.group(1), match.group(2), match.group(3)

        # Try simple owner/repo format
        else:
            # First try to extract any ref
            tree_parts = value.split("/tree/")
            blob_parts = value.split("/blob/")

            if len(tree_parts) > 1:
                value, ref = tree_parts[0], tree_parts[1]
            elif len(blob_parts) > 1:
                value, ref = blob_parts[0], blob_parts[1]

            # Now check for owner/repo pattern
            match = cls.SIMPLE_PATTERN.match(value)
            if match:
                namespace, repo = match.group(1), match.group(2)

        if not namespace or not repo:
            raise ValueError(f"Invalid GitHub repository format: {value}")

        repo = repo.removesuffix(".git")

        obj = super().__new__(cls, f"{namespace}/{repo}@{ref}")

        obj.namespace = namespace
        obj.repo = repo
        obj.ref = ref

        return obj

    @property
    def zip_url(self) -> str:
        """ZIP archive URL for the repository."""
        return f"https://github.com/{self.namespace}/{self.repo}/zipball/{self.ref}"

    @property
    def api_zip_url(self) -> str:
        """API ZIP archive URL for the repository."""
        return f"https://api.github.com/repos/{self.namespace}/{self.repo}/zipball/{self.ref}"

    @property
    def tree_url(self) -> str:
        """URL to view the tree at this reference."""
        return f"https://github.com/{self.namespace}/{self.repo}/tree/{self.ref}"

    def __repr__(self) -> str:
        return f"GithubRepo(namespace='{self.namespace}', repo='{self.repo}', ref='{self.ref}')"
