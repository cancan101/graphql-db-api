from typing import Any, Dict, Tuple

from shillelagh.backends.apsw.dialects.base import APSWDialect
from sqlalchemy.engine.url import URL

# -----------------------------------------------------------------------------


class APSWGraphQLDialect(APSWDialect):
    supports_statement_cache = False

    def __init__(
        self,
        **kwargs: Any,
    ):
        super().__init__(safe=True, adapters=["graphql"], **kwargs)

    #     def get_table_names(
    #         self, connection: _ConnectionFairy, schema: str = None, **kwargs: Any
    #     ) -> List[str]:

    def create_connect_args(
        self,
        url: URL,
    ) -> Tuple[Tuple[()], Dict[str, Any]]:
        args, kwargs = super().create_connect_args(url)

        if "adapter_kwargs" in kwargs and kwargs["adapter_kwargs"] != {}:
            raise ValueError(
                f"Unexpected adapter_kwargs found: {kwargs['adapter_kwargs']}"
            )

        # do we want to do this parsing here or in the adapter?
        # Probably here since we are bastardizing the url
        is_https = url.query.get("is_https", "1") != "0"
        adapter_kwargs = {
            "graphql": {
                "host": url.host,
                "port": url.port,
                "path": url.database,
                "is_https": is_https,
            }
        }

        # this seems gross, esp the path override. unclear why memory has to be set here
        return args, dict(kwargs, path=":memory:", adapter_kwargs=adapter_kwargs)
