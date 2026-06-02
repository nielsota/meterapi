from sqlmodel import Session


class _RepoBase:
    """Shared base so mixins can type-annotate self.session without circular imports."""

    session: Session

    def __init__(self, session: Session) -> None:
        self.session = session
