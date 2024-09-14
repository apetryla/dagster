from typing import TYPE_CHECKING, Callable, Optional, Union

from typing_extensions import TypeAlias

from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.decorators.op_decorator import is_context_provided
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError
from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryLoadData

DefinitionsLoadFn: TypeAlias = Union[
    Callable[["DefinitionsLoadContext"], Definitions],
    Callable[[], Definitions],
]


class DefinitionsLoadContext:
    """Holds data that's made available to Definitions-loading code when a DefinitionsLoader is
    invoked.
    User construction of this object is not supported.
    """

    def __init__(self, repository_load_data: Optional["RepositoryLoadData"] = None):
        self._repository_load_data = repository_load_data


@record
class DefinitionsLoader:
    """An object that can be invoked to load a set of definitions."""

    load_fn: DefinitionsLoadFn

    @property
    def has_context_param(self) -> bool:
        return is_context_provided(get_function_params(self.load_fn))

    def __call__(self, context: Optional[DefinitionsLoadContext] = None) -> Definitions:
        """Load a set of definitions using the load_fn provided at construction time.

        Args:
            context (Optional[DefinitionsLoadContext]): If the load_fn requires a context object,
                this object must be provided. If the load_fn does not require a context object,
                this object must be None.

        Returns:
            Definitions: The loaded definitions.
        """
        if self.has_context_param:
            if context is None:
                raise DagsterInvalidInvocationError(
                    "Invoked a DefinitionsLoader that requires a DefinitionsLoadContext without providing one."
                )
            result = self.load_fn(context)  # type: ignore  # (has_context_param type-checker illegible)
        else:
            if context is not None:
                raise DagsterInvalidInvocationError(
                    "Passed a DefinitionsLoadContext to a DefinitionsLoader that does not accept one."
                )
            result = self.load_fn()  # type: ignore  # (has_context_param type-checker illegible)
        if not isinstance(result, Definitions):
            raise DagsterInvariantViolationError(
                "DefinitionsLoader must return a Definitions object"
            )
        return result
